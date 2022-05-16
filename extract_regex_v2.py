import re

keywords = [
    'abstract', 'arguments',  'boolean',  'break',
    'byte',     'case',       'catch',    'char',
    'const',    'continue',   'debugger', 'default',
    'delete',   'do',         'double',   'else',
    'eval',	    'false',      'final',    'finally',
    'float',    'for',        'function', 'goto',
    'if',       'implements', 'in',       'instanceof',
    'int',      'interface',  'let',      'long',
    'native',   'new',        'null',     'package',
    'private',  'protected',  'public',   'return',
    'short',    'static',     'switch',   'synchronized',
    'this',     'throw',      'throws',   'transient',
    'true',     'try',        'typeof',   'var',
    'void',     'volatile',   'while',    'with',
    'yield',    'class',      'enum',     'export',
    'extends',  'import',     'super',
]

func_names = [
    'eval',              'isFinite',      'isNaN',
    'parseFloat',        'parseInt',      'encodeURI',
    'encodeURIComponent','decodeURI',     'decodeURIComponent',
    'escape',            'unescape',      'uneval',
    'length',            'constructor',   'anchor',
    'big',               'blink',         'bold',
    'charAt',            'charCodeAt',    'codePointAt',
    'concat',            'endsWith',      'fontcolor',
    'fontsize',          'fixed',         'includes',
    'indexOf',           'italics',       'lastIndexOf',
    'link',              'localeCompare', 'match',
    'matchAll',          'normalize',     'padEnd',
    'padStart',          'repeat',        'replace',
    'replaceAll',        'search',        'slice',
    'small',             'split',         'strike',
    'sub',               'substr',        'substring',
    'sup',               'startsWith',    'toString',
    'trim',              'trimStart',     'trimLeft',
    'trimEnd',           'trimRight',     'toLocaleLowerCase',
    'toLocaleUpperCase', 'toLowerCase',   'toUpperCase',
    'valueOf',           'at'
]

endmark_list = [
    "\\n",
    "...\\n\" ) ),",
    "...\\n\\n"
]

string_regex = re.compile(r'((?<!\\)\'.*?(?<!\\)\'|(?<!\\)\".*?(?<!\\)\"|(?<!\\)`.*?(?<!\\)`|(?<!\\)/.*?(?<!\\)/[dgimsuy]?|(?:\'|"|\`|/).*\Z)')
# variable_regex = re.compile(r"\b([a-zA-Z_$][\w$]*)\b")
# variable_regex = re.compile(r"([a-zA-Z_$][\w$]*)")
variable_regex = re.compile(r"[^a-zA-Z0-9_$]([a-zA-Z_$][\w$]*)\b")
split_regex = re.compile(r"([a-zA-Z_$][\w$]*|\\\s|\s)")

endmark_regex = re.compile('|'.join([re.escape(i)+"$" for i in endmark_list]))
comment_regex = re.compile(r"//.*\\\\x0a|//.*\.\.\.\\n\\n|//.*\.\.\.\\n\" \) \),")
hexchar_regex = re.compile(r"\\\\x[0-9a-z]{2}")
space_regex   = re.compile(r"[\t\n\r\f\v]+| [ ]+")
clean_space_regex = re.compile(r"(. [^$\w]+ .?|[^$\w]+ .?|.? [^$\w]+)")
semistr_regex = re.compile(r'(?:\'|"|\`|/).*\Z')

var_regex_str = r"[a-zA-Z_$][\w$]*?" #[a-zA-Z0-9_$]

class CodeRegexExtractor(object):

    def __init__(self):
        pass

    def run(self, snippet):
        if not self.clean(snippet):
            return None

        self.var_list = variable_regex.findall(self.snippet)
        # self.strings = list(map(re.escape, self.strings))

        self.split_snippet()
        self.check_snippet()
        self.replacing()

        return self.wrap()
    
    def clean(self, snippet:str):
        # 0. clean the comment
        snippet = comment_regex.sub("", snippet)
        # 1. convert hex char
        snippet = hexchar_regex.sub(lambda c: bytearray.fromhex(c.group(0)[-2:]).decode(), snippet)
        # 2. clean the repeated space characters
        snippet = space_regex.sub("", snippet)
        # 3. clean the endmark
        snippet = endmark_regex.sub("", snippet)
        ## determine whether this snippet contains enough information
        if len(snippet) <= 34: return False
        # 4. replace ' and "
        snippet = snippet.replace("\\\"", '"').replace("\\'", "'")
        # 5. unescape "\\\\"
        snippet = snippet.replace("\\\\", "\\")
        # 6. clean the single space character and semicolon before }
        snippet = self.second_clean(snippet)

        self.snippet = snippet
        # # 7. escape characters in snippet, and escape the special character $, which is often used for defining a variable in js
        # self.snippet = re.escape(snippet).replace("\$","$")
        # return snippet.replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"")
        return True

    def wrap(self):
        # ignore the first function name
        self.code_regex = self.code_regex.replace("\\ [a-zA-Z_$][\\w$]*?", "(\\ [a-zA-Z_$][\\w$]*?)?", 1)
        return self.code_regex

    def second_clean(self, snippet):
        self.strings = string_regex.findall(snippet)
        cleaned = ""
        for substr in string_regex.split(snippet):
            if substr in self.strings:
                cleaned += substr
                continue
            tmp = clean_space_regex.sub(lambda obj: obj.group(0).replace(" ", ''), substr)
            cleaned += tmp.replace(";}", "}")
        
        return cleaned

    def split_snippet(self):
        parts = [part for part in string_regex.split(self.snippet) if part]
        words = []
        for part in parts:
            if part in self.strings: 
                words.append(part)
                continue
            words.extend([word for word in split_regex.split(part) if word])

        self.words = words

    def check_snippet(self):
        # add a pseudo-name to the snippet that does not have a function name
        if self.words[1].startswith("("):
            self.words.insert(1, " ")
            self.words.insert(2, "functionName")
            self.var_list.append("functionName")

        # delete the last word if it is incomplete
        if self.words[-1] in self.var_list and self.words[-1] not in keywords:
            self.words.pop()

    def replacing(self):
        code_regex = ""
        for word in self.words:

            if word in self.strings:
                if word[0] in ['`', '/']:
                    code_regex += re.escape(word)
                    continue
                if len(word) == 1 or word[-1] not in ['\'', '"']:
                    word = word[1:]
                    code_regex += "('|\")" + re.escape(word)
                else:
                    word = word[1:-1]
                    code_regex += "('|\")" + re.escape(word) + "('|\")"
                continue
            
            if word in keywords or word in func_names:
                code_regex += re.escape(word)
                continue

            if word not in self.var_list:
                code_regex += re.escape(word)
                continue

            code_regex += var_regex_str
            
        self.code_regex = code_regex


def main():
    cre = CodeRegexExtractor()
    s = "function $t(_0x5a0cb2){var _0xde0fc6=_0x31c04c>-0x1?_0x5a0cb2[_0x45ec('0x56')](0x0,_0x31c04c):_0x5a0cb2;var _0x8f1dd5=_0x31c04c>-0x1?_0x18b508(_0x5a0cb2["
    regex = cre.run(s)
    print(regex)
    print(re.match(regex, s))


if __name__ == "__main__":
    main()