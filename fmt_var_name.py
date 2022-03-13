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
if_start_regex = re.compile(r'(if\s*\(.*?\)\s*{)')
else_regex = re.compile(r'else\s*{')



class FormatVarName(object):
    def __init__(self, jscode):
        self.jscode = jscode.strip()
        self.stack = 0    
        self.varNameGen = self.var_name_gen()
        self.repl_var_hashMap = defaultdict(lambda: defaultdict(list))

    def run(self, stmts):
        self.strings = string_regex.findall(self.jscode)
        self.funcs = {func_start: (func_name.strip(), params) for func_start, func_name, params in function_start_regex.findall(self.jscode)}
        self.for_stmts = for_start_regex.findall(self.jscode)
        self.while_stmts = while_start_regex.findall(self.jscode)
        self.if_stmts = if_start_regex.findall(self.jscode)

        self.split2statements()
        self.renew_code(stmts)

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

    def renew_code(self, stmts):
        new_code = []
        self.state_stack = []

        for stmt in stmts:
            sub_stmts = self._split2sub_stmts(stmt)
            flag = True if sub_var_regex.match(stmt) else False
            for sub_stmt in sub_stmts:
                new_stmt = self._repl_stmt(sub_stmt, flag)
                new_code.append(new_stmt)

        self.new_code = "".join(new_code)

    def _split2sub_stmts(self, stmt):
        parts_1 = [part.strip() for part in string_regex.split(stmt) if part]    
        parts_2 = []

        for parts in parts_1:
            if parts in self.strings: 
                parts_2.append(parts)
                continue
            parts_2.extend([part for __parts in function_split_regex.split(parts)
                                    for _parts in for_start_regex.split(__parts)
                                        for part in while_start_regex.split(_parts) if part])
        return parts_2

    def _repl_stmt(self, stmt, flag):
        if stmt in self.strings:
            return stmt

        if stmt in self.funcs:
            self.state_stack.append("func")
            func_name, params = self.funcs[stmt]
            param_list = [param.strip(". ") for param in params.split(",")]
            self.stack += 1
            if func_name: self.update_var_hashMap(self.stack-1, func_name)
            self.update_var_hashMap(self.stack, *param_list)

        if any([fs.startswith(stmt) for fs in self.for_stmts]):
            self.state_stack.append("for")
            self.stack += 1
            if matched := let_define_regex.search(stmt):
                self.state_stack.append("for+let")
                variables = matched.group(1)
                var_list = [var.split("=")[0].strip("; ") for var in variables.split(",")  if sub_var_regex.match(var)]
                self.update_var_hashMap(self.stack, *var_list)
                if ";" in stmt: self.state_stack.pop()
            
            elif matched := var_define_regex.search(stmt):
                self.state_stack.append("for+var")
                variables = matched.group(1)
                var_list = [var.split("=")[0].strip("; ") for var in variables.split(",")  if sub_var_regex.match(var)]
                self.update_var_hashMap(self.stack-1, *var_list)
                if ";" in stmt: self.state_stack.pop()
        
        elif self.state_stack and (self.state_stack[-1] == "for+var" or self.state_stack[-1] == "for+let"):
            variables = stmt.split(";", 1)[0]
            var_list = [var.split("=")[0].strip("; ") for var in variables.split(",") if sub_var_regex.match(var)]
            stk = self.stack if self.state_stack[-1] == "for+let" else self.stack-1
            self.update_var_hashMap(stk, *var_list)
            if ";" in stmt: self.state_stack.pop()

        if stmt in self.while_stmts:
            self.state_stack.append("while")
            self.stack += 1

        if stmt in self.if_stmts:
            self.state_stack.append("if")
            self.stack += 1

        if else_regex.search(stmt):
            self.state_stack.append("else")
            self.stack += 1

        if stmt.startswith("}"):
            self.state_stack.pop()
            self.stack -= 1

        if matched := var_define_regex.match(stmt):
            self.state_stack.append("var")
            variables = matched.group(1)
            var_list = [var.split("=")[0].strip("; ") for var in variables.split(",") if var]
            self.update_var_hashMap(self.stack, *var_list)
            if stmt[-1] == ";": self.state_stack.pop()

        elif self.state_stack and self.state_stack[-1] == "var" and flag:
            var_list = [var.split("=")[0].strip("; ") for var in stmt.split(",") if sub_var_regex.match(var)]
            self.update_var_hashMap(self.stack, *var_list)
            if stmt[-1] == ";": self.state_stack.pop()          

        new_stmt = self.repl_helper(stmt)
        return new_stmt

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


def get_hash(filename):
    stmts = []
    with open(filename, "r") as f:
        line = f.readline()
        while line:
            line = line.strip()
            stmts.append(line)
            line = f.readline()

    jscode = "".join(stmts)
    print(jscode)
    # md5 = hashlib.md5(jscode.encode('utf-8'))
    # print(md5.hexdigest())
    fvn = FormatVarName(jscode)
    new_code = fvn.run(stmts)
    # print(new_code)
    md5 = hashlib.md5(new_code.encode('utf-8'))
    return md5.hexdigest()

def test():
    sample_md5 = get_hash("./sample.js")
    target_md5 = get_hash("./target.js")
    # print(sample_md5)
    # print(target_md5)
    # print(sample_md5 == target_md5)

if __name__ == "__main__":
    test()