from collections import defaultdict
from pprint import pprint
import re
import hashlib

from snippet_cleaner import cleaner

string_regex = re.compile(r'((?<!\\)\'.*?(?<!\\)\'|(?<!\\)\".*?(?<!\\)\"|(?<!\\)`.*?(?<!\\)`)')
function_start_regex = re.compile(r'(function(\s+\w+|\s*)\s*\(([^\)]*)\)\s*{)')
function_split_regex = re.compile(r'(function\s+\w+\s*\([^\)]*\)\s*{|function\s*\([^\)]*\)\s*{)')
var_define_regex = re.compile(r'var\s+(.*)')
sub_var_regex = re.compile(r'^\s*[a-zA-Z_$][\w$]*\s*[=,;]?')
let_define_regex = re.compile(r'let\s+([\w$,= ]+)\s*;')
for_start_regex = re.compile(r'(for\s*\(.*)')
while_start_regex = re.compile(r'(do\s*{|while\s*\(.*?\)\s*{)')
var_regex_str = r"[a-zA-Z_$][\w$]*?" #[a-zA-Z0-9_$]


keywords = [
    'abstract', 'arguments','boolean',  'break',
    'byte',     'case',     'catch',    'char',
    'const',    'continue', 'debugger', 'default',
    'delete',   'do',       'double',   'else',
    'eval',	    'false',    'final',    'finally',
    'float',    'for',      'function', 'goto',
    'if',       'implements', 'in',     'instanceof',
    'int',      'interface','let',      'long',
    'native',   'new',      'null',     'package',
    'private',  'protected','public',   'return',
    'short',    'static',   'switch',   'synchronized',
    'this',     'throw',    'throws',   'transient',
    'true',     'try',      'typeof',   'var',
    'void',     'volatile', 'while',    'with',
    'yield',    'class',    'enum',     'export',
    'extends',  'import',   'super',
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

string_regex = re.compile(r'((?<!\\)\'.*?(?<!\\)\'|(?<!\\)\".*?(?<!\\)\"|(?<!\\)`.*?(?<!\\)`|(?<!\\)/.*?(?<!\\)/[dgimsuy]?)')
variable_regex = re.compile(r"([a-zA-Z_$][\w$]*)")
split_regex = re.compile(r"([a-zA-Z_$][\w$]*|\s)")

endmark_regex = re.compile('|'.join([re.escape(i)+"$" for i in endmark_list]))
comment_regex = re.compile(r"//.*\\\\x0a|//.*\.\.\.\\n\\n|//.*\.\.\.\\n\" \) \),")
hexchar_regex = re.compile(r"\\\\x[0-9a-z]{2}")
space_regex   = re.compile(r"[\t\n\r\f\v]+| [ ]+")


class CodeRegexExtractor(object):

    def __init__(self):
        pass

    def run(self, snippet):
        if not self.clean(snippet):
            return None

        self.var_list = variable_regex.findall(self.snippet)
        self.strings = string_regex.findall(self.snippet)

        self.split_snippet()
        self.replacing()

        return self.wrap()
    
    def clean(self, snippet:str):
        # 0. clean the comment
        snippet = comment_regex.sub("", snippet)
        # 1. convert hex char
        snippet = hexchar_regex.sub(lambda c: bytearray.fromhex(c.group(0)[-2:]).decode(), snippet)
        # 2. clean the space characters
        snippet = space_regex.sub("", snippet)
        # 3. clean the endmark
        snippet = endmark_regex.sub("", snippet)
        ## determine whether this snippet contains enough information
        if len(snippet) <= 34: return False
        # 4. replace ' and "
        snippet = snippet.replace("\\\"", '"').replace("\\'", "'")
        # 5. escape characters in snippet, and escape the special character $, which is often used for defining a variable in js
        self.snippet = re.escape(snippet).replace("\$","$")
        # return snippet.replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"")
        return True

    def wrap(self):
        return self.code_regex
        # return self.code_regex.replace("\n", "\\n").replace("\t", "\\t").replace("\"", "\\\"")

    def split_snippet(self):
        parts = [part for part in string_regex.split(self.snippet) if part]
        words = []
        for part in parts:
            if part in self.strings: 
                words.append(part)
                continue
            words.extend([word for word in split_regex.split(part) if word])

        self.words = words

    def replacing(self):
        code_regex = ""
        for word in self.words:

            if word in self.strings:
                word = word[1:-1]
                code_regex += re.escape("('|\")") + word + re.escape("('|\")")
            
            if word in keywords or word in func_names:
                code_regex += word
                continue

            # if '\\}' in word:
            #     code_regex += word.replace('\\}', ';?\\}')

            if word not in self.var_list:
                code_regex += word
                continue

            code_regex += var_regex_str
            
        self.code_regex = code_regex



def test():
    cre = CodeRegexExtractor()
    # sample = 'function(O, T) {var N = T.split("="),S = t(N[0]),M,R = K,P = 0,U = S.split("]["),Q = U.length - 1;if (/\[/.test(U[0]) && /\]$/.test(U[Q])) {U[Q] = U[Q].replace(/\]$/, "");U = U.shift().split("[").concat(U);Q = U.length - 1;} else {Q = 0;}if (N.length === 2) {M = t(N[1]);if (I) {M = M && !isNaN(M) ? +M : M === "undefined" ? h : J[M] !== h ? J[M] : M;}if (Q) {for (; P <= Q; P++) {S = U[P] === "" ? R.length : U[P];R = R[S] = P < Q ? R[S] || (U[P + 1] && isNaN(U[P + 1]) ? {} : []) : M;}} else {if ($.isArray(K[S])) {K[S].push(M);} else {if (K[S] !== h) {K[S] = [K[S], M];} else {K[S] = M;}}}} else {if (S) {K[S] = I ? h : "";}}}'
    # target = 'function(L, Q) {var K = Q.split("="),P = r(K[0]),J,O = H,M = 0,R = P.split("]["),N = R.length - 1;if (/\[/.test(R[0]) && /\]$/.test(R[N])) {R[N] = R[N].replace(/\]$/, "");R = R.shift().split("[").concat(R);N = R.length - 1;} else {N = 0;}if (K.length === 2) {J = r(K[1]);if (F) {J = J && !isNaN(J) ? +J : J === "undefined" ? i : G[J] !== i ? G[J] : J;}if (N) {for (; M <= N; M++) {P = R[M] === "" ? O.length : R[M];O = O[P] = M < N ? O[P] || (R[M + 1] && isNaN(R[M + 1]) ? {} : []) : J;}} else {if ($.isArray(H[P])) {H[P].push(J);} else {if (H[P] !== i) {H[P] = [H[P], J];} else {H[P] = J;}}}} else {if (P) {H[P] = F ? i : "";}}}'
    # sample_regex = cre.run(sample)
    # print(sample_regex)
    # if re.match(sample_regex, sample):
    #     print("Matched!")
    # else:
    #     print("Unmatched.")
    # print("--------------------------------------------")
    # problem: cannot match escape characters
    # uncmpl_sample = "function (t){var t=t?t.split(\\\"?\\\")[1]:window.location.search.slice(1),r={};if(t)for(var e=(t=t.split(\\\"#\\\")[0]).split(\\\"&\\\"),n=0;n<e.length;n++){var i,o=e[n].split(\\\"=\\\"),a=o[0],s=void 0===o[1]||o[1],a=a.toLowerCase();\\\"string\\\"==typeof s&&(s=s.toLowerCase()),a.match(/\\\\[(\\\\d+)?\\\\]$/)?(r[i=a.replace(/\\\\[(\\\\d+)?\\\\]/,\\\"\\\")]||(...\\n\\n"
    # uncmpl_target = "function (e){var e=e?e.split(\\\"?\\\")[1]:window.location.search.slice(1),t={};if(e)for(var n=(e=e.split(\\\"#\\\")[0]).split(\\\"&\\\"),o=0;o<n.length;o++){var i,r=n[o].split(\\\"=\\\"),d=r[0],a=void 0===r[1]||r[1],d=d.toLowerCase();\\\"string\\\"==typeof a&&(a=a.toLowerCase()),d.match(/\\\\[(\\\\d+)?\\\\]$/)?(t[i=d.replace(/\\\\[(\\\\d+)?\\\\]/,\\\"\\\")]||(...\\n\\n"
    # uncmpl_regex = cre.run(uncmpl_sample)
    # print(uncmpl_regex)
    # print(cleaner(uncmpl_target))
    # print(re.search(uncmpl_regex, cleaner(uncmpl_target)))
    s = "function l(e,t,i,n){var s=e.shift();if(!s){if(p(t[i])){t[i].push(n)}else if(\"object\"==typeof t[i]){t[i]=n}else if(\"undefined\"==typeof t[i]){t[i]=n}else{t[i]=[t[i],n]}}else{v"
    print(cre.run(s))


if __name__ == "__main__":
    test()
    # test_str = 'function getQueryParams(qs){if(typeof qs===\\"undefined\\"){qs=location.search}qs=qs.replace(/\\\\+/g,\\" \\");var params={},tokens,re=/[?&]?([^=]+)=([^&]*)/g;while(tokens=re.exec(qs)){var name=decodeURIComponent(tokens[1]);var value=decodeURIComponent(tokens[2]);if(value.length==0){continue}if(name.substr(-2)==\\"[]\\"){name=name.subst...\\n\\n'
    # print(test_str[:50])
    # test_str.replace("\\\\", "\\")
    # print(test_str[:50])