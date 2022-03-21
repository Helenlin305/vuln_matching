from collections import defaultdict
from pprint import pprint
import re
import hashlib

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

string_regex = re.compile(r'((?<!\\)\'.*?(?<!\\)\'|(?<!\\)\".*?(?<!\\)\"|(?<!\\)`.*?(?<!\\)`|(?<!\\)/.*?(?<!\\)/[dgimsuy]?)')
variable_regex = re.compile(r"([a-zA-Z_$][\w$]*)")
split_regex = re.compile(r"([a-zA-Z_$][\w$]*|\s)")

end_mark = "...\\n\\n"

class CodeRegexExtractor(object):

    def __init__(self):
        pass

    def run(self, snippet):
        self.snippet = self.clean(snippet)
        self.var_list = variable_regex.findall(self.snippet)
        self.strings = string_regex.findall(self.snippet)

        self.split_snippet()
        self.replacing()

        return self.wrap()
    
    def clean(self, snippet:str):
        return re.escape(snippet).replace("\$","$")
        # return snippet.replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"")

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

            if word in self.strings \
                or word in keywords or word in func_names:
                code_regex += word
                continue

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
    uncmpl_sample = 'function (str){if(\\"string\\"!=typeof str)return{};str=trim(str);if(\\"\\"==str)return{};if(\\"?\\"==str.charAt(0))str=str.slice(1);var obj={};var pairs=str.split(\\"&\\");for(var i=0;i<pairs.length;i++){var parts=pairs[i].split(\\"=\\");var key=decode(parts[0]);var m;if(m=pattern.exec(key)){obj[m[1]]=obj[m[1]]||[];obj[m[1]][m...\\n\\n'
    uncmpl_target = 'function (sss){if(\\"string\\"!=typeof sss)return{};str=trim(str);if(\\"\\"==str)return{};if(\\"?\\"==str.charAt(0))str=str.slice(1);var obj={};var pairs=str.split(\\"&\\");for(var i=0;i<pairs.length;i++){var parts=pairs[i].split(\\"=\\");var key=decode(parts[0]);var m;if(m=pattern.exec(key)){obj[m[1]]=obj[m[1]]||[];obj[m[1]][m...\\n\\n'
    uncmpl_regex = cre.run(uncmpl_sample)
    print(uncmpl_regex)
    print(re.match(uncmpl_regex, uncmpl_target))


if __name__ == "__main__":
    test()
    # test_str = 'function getQueryParams(qs){if(typeof qs===\\"undefined\\"){qs=location.search}qs=qs.replace(/\\\\+/g,\\" \\");var params={},tokens,re=/[?&]?([^=]+)=([^&]*)/g;while(tokens=re.exec(qs)){var name=decodeURIComponent(tokens[1]);var value=decodeURIComponent(tokens[2]);if(value.length==0){continue}if(name.substr(-2)==\\"[]\\"){name=name.subst...\\n\\n'
    # print(test_str[:50])
    # test_str.replace("\\\\", "\\")
    # print(test_str[:50])