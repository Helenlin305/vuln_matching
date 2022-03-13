import re
from collections import defaultdict
import hashlib

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

string_regex = re.compile(r'((?<!\\)\'.*?(?<!\\)\'|(?<!\\)\".*?(?<!\\)\"|(?<!\\)`.*?(?<!\\)`|(?<!\\)/.*?(?<!\\)/[dgimsuy]?)')
variable_regex = re.compile(r"([a-zA-Z_$][\w$]*)")
split_regex = re.compile(r"([a-zA-Z_$][\w$]*|\s)")

end_mark = "...\\n\\n"

class ReplaceVarName(object):

    def __init__(self, snippet:str):
        self.snippet = self.clean(snippet)
        self.varNameGen = self.var_name_gen()
        self.repl_var_hashMap = defaultdict(lambda: defaultdict(list))

    def run(self):
        self.var_list = variable_regex.findall(self.snippet)
        self.strings = string_regex.findall(self.snippet)

        self.split_snippet()
        self.replacing()

        return self.wrap()

    def var_name_gen(self):
        name_list = ['']
        while True:
            for i in range(26):
                name = name_list[0] + chr(65+i)
                name_list.append(name)
                yield name
            name_list.pop(0)    
    
    def clean(self, snippet:str):
        return snippet.replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"")

    def wrap(self):
        return self.new_code.replace("\n", "\\n").replace("\t", "\\t")

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
        new_code = ""
        self.stack = 0
        func_flag = False

        for word in self.words:
            if word == 'function': func_flag = True

            if word in self.strings \
                or word in keywords or word in func_names:
                new_code += word
                continue
            
            if "}" in word: self.stack -= word.count("}")
            if "{" in word: 
                self.stack += word.count("{")
                if func_flag: func_flag = False

            if word not in self.var_list:
                new_code += word
                continue

            new_code += self.update_var(word, func_flag)
            
        self.new_code = new_code

    def update_var(self, variable, func_flag):
        if func_flag:
            new_name = next(self.varNameGen)
            self.repl_var_hashMap[self.stack+1][variable] = new_name
            return new_name

        stk = self.stack
        while stk >= 0:
            if stk in self.repl_var_hashMap and variable in self.repl_var_hashMap[stk]:
                return self.repl_var_hashMap[stk][variable]
            stk -= 1

        new_name = next(self.varNameGen)
        self.repl_var_hashMap[self.stack][variable] = new_name

        return new_name


def get_hash(code_snippet):
    rvn = ReplaceVarName(code_snippet)
    new_code = rvn.run()
    print(new_code)
    md5 = hashlib.md5(new_code.encode('utf-8'))
    return md5.hexdigest()


def test():
    sample = 'function(O, T) {var N = T.split("="),S = t(N[0]),M,R = K,P = 0,U = S.split("]["),Q = U.length - 1;if (/\[/.test(U[0]) && /\]$/.test(U[Q])) {U[Q] = U[Q].replace(/\]$/, "");U = U.shift().split("[").concat(U);Q = U.length - 1;} else {Q = 0;}if (N.length === 2) {M = t(N[1]);if (I) {M = M && !isNaN(M) ? +M : M === "undefined" ? h : J[M] !== h ? J[M] : M;}if (Q) {for (; P <= Q; P++) {S = U[P] === "" ? R.length : U[P];R = R[S] = P < Q ? R[S] || (U[P + 1] && isNaN(U[P + 1]) ? {} : []) : M;}} else {if ($.isArray(K[S])) {K[S].push(M);} else {if (K[S] !== h) {K[S] = [K[S], M];} else {K[S] = M;}}}} else {if (S) {K[S] = I ? h : "";}}}'
    target = 'function(L, Q) {var K = Q.split("="),P = r(K[0]),J,O = H,M = 0,R = P.split("]["),N = R.length - 1;if (/\[/.test(R[0]) && /\]$/.test(R[N])) {R[N] = R[N].replace(/\]$/, "");R = R.shift().split("[").concat(R);N = R.length - 1;} else {N = 0;}if (K.length === 2) {J = r(K[1]);if (F) {J = J && !isNaN(J) ? +J : J === "undefined" ? i : G[J] !== i ? G[J] : J;}if (N) {for (; M <= N; M++) {P = R[M] === "" ? O.length : R[M];O = O[P] = M < N ? O[P] || (R[M + 1] && isNaN(R[M + 1]) ? {} : []) : J;}} else {if ($.isArray(H[P])) {H[P].push(J);} else {if (H[P] !== i) {H[P] = [H[P], J];} else {H[P] = J;}}}} else {if (P) {H[P] = F ? i : "";}}}'
    sample_md5 = get_hash(sample)
    target_md5 = get_hash(target)
    print(sample_md5)
    print(target_md5)
    if sample_md5 == target_md5:
        print("Matched!")
    else:
        print("Unmatched.")

    uncmpl_sample = 'function getQueryParams(qs){if(typeof qs===\\"undefined\\"){qs=location.search}qs=qs.replace(/\\\\+/g,\\" \\");var params={},tokens,re=/[?&]?([^=]+)=([^&]*)/g;while(tokens=re.exec(qs)){var name=decodeURIComponent(tokens[1]);var value=decodeURIComponent(tokens[2]);if(value.length==0){continue}if(name.substr(-2)==\\"[]\\"){name=name.subst...\\n\\n'
    print(get_hash(uncmpl_sample))



if __name__ == "__main__":
    test()