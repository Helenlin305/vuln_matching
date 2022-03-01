from collections import defaultdict
from pprint import pprint
import re

string_regex = re.compile(r'((?<!\\)\'.*?(?<!\\)\'|(?<!\\)\".*?(?<!\\)\"|(?<!\\)`.*?(?<!\\)`)')
function_start_regex = re.compile(r'(function(\s+\w+|\s*)\s*\(([^\)]*)\)\s*{)')
function_split_regex = re.compile(r'(function\s+\w+\s*\([^\)]*\)\s*{|function\s*\([^\)]*\)\s*{)')
var_define_regex = re.compile(r'var\s+(.*)')
let_define_regex = re.compile(r'let\s+([\w$,= ]+)\s*;')
for_start_regex = re.compile(r'(for\s*\(.*?\)\s*{)')
while_start_regex = re.compile(r'(do\s*{|while\s*\(.*?\)\s*{)')


class FormatVarName(object):
    def __init__(self, jscode):
        self.jscode = jscode.strip()
        self.stack = 0    
        self.varNameGen = self.var_name_gen()
        self.repl_var_hashMap = defaultdict(lambda: defaultdict(list))

    def run(self):
        self.strings = string_regex.findall(self.jscode)
        self.funcs = {func_start: (func_name.strip(), params) for func_start, func_name, params in function_start_regex.findall(self.jscode)}
        self.for_stmts = for_start_regex.findall(self.jscode)
        self.while_stmts = while_start_regex.findall(self.jscode)

        self.split2statements()
        self.renew_code()

        return self.new_code

        
    def var_name_gen(self):
        name_list = ['']
        while True:
            for i in range(26):
                name = name_list[0] + chr(65+i)
                name_list.append(name)
                yield name
            name_list.pop(0)

    def split2statements(self):
        stmts = []
        
        parts_1 = [part.strip() for part in string_regex.split(self.jscode)]    
        parts_2 = []

        # 1. split by functions, for/while loops while ignoring strings
        for parts in parts_1:
            if parts in self.strings: 
                parts_2.append(parts)
                continue
            parts_2.extend([part for __parts in function_split_regex.split(parts)
                                    for _parts in for_start_regex.split(__parts)
                                        for part in while_start_regex.split(_parts) ])

        # 2. split by ';' while ignoring strings and for loops
        for parts in parts_2:
            if parts in self.strings or parts in self.for_stmts: 
                stmts.append(parts)
                continue
            stmts.extend([stmt.strip() for stmt in re.split("(.*?[;}])", parts) if stmt.strip()])

        # 3. Merge into the statement splited by strings
        i = 0
        ends_regex = re.compile(".*?[;{}]\s*$")
        while i < len(stmts):
            cur_stmt = stmts[i]
            nxt_stmt = stmts[i+1] if i+1 < len(stmts) else None
            while not (ends_regex.match(cur_stmt) or nxt_stmt in self.funcs):
                cur_stmt += stmts.pop(i+1)
            stmts[i] = cur_stmt
            i += 1

        self.stmts = stmts

    def update_var_hashMap(self, stack, *var_list):
        for var in var_list:
            self.repl_var_hashMap[stack][var] = next(self.varNameGen)

    def _repl(self, matchobj):
        var = matchobj.group(0)
        stack = self.stack
        while stack >= 0:
            if stack in self.repl_var_hashMap and var in self.repl_var_hashMap[stack]:
                return self.repl_var_hashMap[stack][var]
            stack -= 1
        return var

    def repl_helper(self, stmt, var_list=None):
        if not var_list:
            var_list = [var for stack in range(self.stack+1) for var in self.repl_var_hashMap[stack]]
        _var_regex = '|'.join([r'\b%s\b' % var for var in var_list])
        var_regex = re.compile(_var_regex)
        new_stmt = var_regex.sub(self._repl, stmt)
        return new_stmt

    def renew_code(self):
        new_code = ""
        
        for stmt in self.stmts:
            state_stack = []
            if stmt in self.funcs:
                func_name, params = self.funcs[stmt]
                param_list = [param.strip(". ") for param in params.split(",")]
                self.stack += 1
                if func_name: self.update_var_hashMap(self.stack-1, func_name)
                self.update_var_hashMap(self.stack, *param_list)

            if stmt in self.for_stmts:
                self.stack += 1
                if matched := let_define_regex.search(stmt):
                    variables = matched.group(1)
                    var_list = [var.split("=")[0].strip("; ") for var in variables.split(",")]
                    self.update_var_hashMap(self.stack, *var_list)
                elif matched := var_define_regex.search(stmt):
                    variables = matched.group(1)
                    var_list = [var.split("=")[0].strip("; ") for var in variables.split(",")]
                    self.update_var_hashMap(self.stack-1, *var_list)
            
            if matched := var_define_regex.match(stmt):
                variables = matched.group(1)
                var_list = [var.split("=")[0].strip("; ") for var in variables.split(",")]
                self.update_var_hashMap(self.stack, *var_list)

            if stmt in self.while_stmts:
                self.stack += 1

            if stmt.startswith("}") or stmt.endswith("}"):
                self.stack -= 1

            new_stmt = self.repl_helper(stmt)
            new_code += new_stmt

        self.new_code = new_code


def test():

    js_snippet = '''
    function foo (a, b, c) {
        var b = 10, s, f, ss;
        s = `asd\`"f{asdf;asdf}a"sdf`;
        f = "";
        console.log(b);
        for (var i=0;i<a.length; i++) {
            s += a[i];
        }
        ss = '"\\'1`23;4{345}"';
        function bar(d) {
            return 10;
        }
        bar(10);
        while (b < 10) {
            b -= 1;
        }
        do {
            b += 1;
        } while (b < 10);
        return s;
    }
    '''
    # js_snippet = '''
    # function thennable(ref, cb, ec, cn) {
    #     if (2 == state) return cn();
    #     if (
    #         ("object" != typeof val && "function" != typeof val) ||
    #         "function" != typeof ref
    #     )
    #         cn();
    #     else
    #         try {
    #         var cnt = 0;
    #         ref.call(
    #             val,
    #             function (v) {
    #             cnt++ || ((val = v), cb());
    #             },
    #             function (v) {
    #             cnt++ || ((val = v), ec());
    #             }
    #         );
    #         } catch (e) {
    #         (val = e), ec();
    #         }
    #     }
    # '''

    js_snippet = " ".join([line.strip() for line in js_snippet.split("\n") if line])
    # js_snippet = 'function (e,t){var n=t===u.length-1,r=!n&&function isStringOfNumbers(e){return e.split(\\"\\").every(function(e){return e.charCodeAt(0)>=48&&e.charCodeAt(0)<=57})}(u[t+1]);s[e]=n?a:s[e]||(r?new Array:{}),n||(s=s[e])}'

    print(js_snippet)
    fvn = FormatVarName(js_snippet)
    print(fvn.run())


if __name__ == "__main__":
    test()