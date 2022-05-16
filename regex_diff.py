import difflib
import re

parentheses = re.compile(r"(?<!\\)(\(|\))")
re_string_regex = re.compile(r'((?<!\\)\(\'\|"\).*?(?<!\\)\(\'\|"\)|(?<!\\)`.*?(?<!\\)`|(?<!\\)/.*?(?<!\\)/[dgimsuy]?|(?:\(\'\|"\)|\`|/).*\Z)')

def is_similar(a, b, threshold=0.85, strict=True):
    s = difflib.SequenceMatcher(None, a, b)
    score0 = s.ratio()

    if strict:
        return score0 >= threshold and min(len(a), len(b)) > 205

    min_len = min(len(a), len(b))
    a = a[:min_len]
    b = b[:min_len]
    s = difflib.SequenceMatcher(None, a, b)
    score1 = s.ratio()
    
    return score0 >= threshold or score1 >= threshold

def get_score(a, b):
    s = difflib.SequenceMatcher(None, a, b)
    score0 = s.ratio()

    min_len = min(len(a), len(b))
    a = a[:min_len]
    b = b[:min_len]
    s = difflib.SequenceMatcher(None, a, b)
    score1 = s.ratio()
    
    return max(score0, score1)

def merge_regex(a, b):
    a_re_idx = parse_regex(a)
    b_re_idx = parse_regex(b)

    match_obj  = get_matched_obj(a, b, a_re_idx, b_re_idx)
    
    new_regex = ""
    pre_i, pre_j = 0, 0
    tmp_a, tmp_b = "", ""
    for i, j, size, ori in match_obj:
        if size == 0:
            tmp_a += a[pre_i:i]
            tmp_b += b[pre_j:j]
            new_regex += _merge_helper(tmp_a, tmp_b)

        elif size > 6:
            if pre_i != i: tmp_a += a[pre_i:i]
            if pre_j != j: tmp_b += b[pre_j:j]
            middle_same, middle_idx = middle_merge(tmp_a, tmp_b)
            tmp_a = tmp_a[:len(tmp_a)-middle_idx]
            tmp_b = tmp_b[:len(tmp_b)-middle_idx]
            new_regex += _merge_helper(tmp_a, tmp_b)
            new_regex += (middle_same + ori)
            pre_i = i + size
            pre_j = j + size
            tmp_a = ""
            tmp_b = ""

    return new_regex

def parse_regex(regex):
    idx_res = parse_parenthesis(regex)
    prth_idx = [items[0] for items in idx_res if items[2] != '(\'|")']

    idx = []
    start = 0
    for beg, end in prth_idx:
        ret = parse_var_regex(regex[start:beg], start)
        idx.extend(ret)
        ret = parse_strings(regex[start:beg], start)
        idx.extend(ret) 
        item = (beg, end)
        idx.append(item)
        start = end
    ret = parse_var_regex(regex[start:len(regex)], start)
    idx.extend(ret)
    ret = parse_strings(regex[start:len(regex)], start)
    idx.extend(ret)

    return idx

def parse_parenthesis(regex):
    retmp = regex[0]
    i = 1
    idx = []
    stk = []
    beg = 0
    if regex[0] == "(": stk.append(0)
    while i < len(regex):
        cur = regex[i]
        pre = regex[i-1]
        retmp += cur
        if cur == "(" and pre != "\\":
            stk.append(i)
        elif cur == ")" and pre != "\\":
            beg = stk.pop()
            if i + 1 < len(regex) and regex[i+1] == "?":
                end = i+1
                retmp += "?"
                i += 1
            else:
                end = i
            item = (beg, end+1)
            idx.append(item)

        i += 1
    
    idx_res = check_parse_regex(regex, idx)
    
    return idx_res

def parse_var_regex(regex, start):
    var_regex  = re.compile("("+re.escape(r"[a-zA-Z_$][\w$]*?")+")")
    parts = var_regex.split(regex)
    var_idx = []
    cur_len = 0
    for part in parts:
        if part != r"[a-zA-Z_$][\w$]*?":
            cur_len += len(part)
            continue
        item = (start+cur_len, start+cur_len+len(part))
        var_idx.append(item)
        cur_len += len(part)

    return var_idx

def parse_strings(regex, start):
    parts = re_string_regex.split(regex)
    strings = re_string_regex.findall(regex)
    str_idx = []
    cur_len = 0
    for part in parts:
        if part not in strings:
            cur_len += len(part)
            continue
        item = (start+cur_len, start+cur_len+len(part))
        str_idx.append(item)
        cur_len += len(part)

    return str_idx

def check_parse_regex(regex, idx):
    return [((beg, end), end-beg, regex[beg:end]) for beg, end in idx]

def get_matched_obj(a, b, i_idx, j_idx, a_start=0, b_start=0): 
    s = difflib.SequenceMatcher(None, a, b)

    match_obj = s.get_matching_blocks()
    final_obj = []
    for i, j, size in match_obj:
        matched = a[i: i+size]
        if size == 0: 
            final_obj.append((a_start+i, b_start+j, size, matched))
            return final_obj
        if in_regex(a_start+i, size, i_idx) or in_regex(b_start+j, size, j_idx):
            continue
        if matched == "\\":
            continue
        if matched[-1] == "\\" and not (i+size == len(a) or j+size == len(b)): 
            matched = matched[:-1]
            size -= 1
            while size > 0 and matched[-1] == "\\":
                matched = matched[:-1]
                size -= 1
            if size > 2:
                final_obj.append((a_start+i, b_start+j, size, matched))
            final_obj.extend(get_matched_obj(a[i+size:], b[j+size:], i_idx, j_idx, i+size+a_start, j+size+b_start))
            break
        if size > 2:
            final_obj.append((a_start+i, b_start+j, size, matched))
        
    return final_obj

def in_regex(idx, size, var_idx):
    cur_set = set(range(idx, idx + size))
    for beg, end in var_idx:
        tmp_set = set(range(beg, end))
        same = tmp_set & cur_set
        if same and same != tmp_set:
            return True
    return False

def middle_merge(tmp_a, tmp_b):
    idx_a = len(tmp_a)
    idx_b = len(tmp_b)
    min_len = min(idx_a, idx_b)
    same = ""
    i = 0
    while i < min_len:
        if tmp_a[idx_a-i-1] != tmp_b[idx_b-i-1]:
            break
        cur = tmp_a[idx_a-i-1]
        if cur in ["(", ")", "?"]:
            break
        same = cur + same
        i += 1

    return same, i

def _merge_helper(tmp_a, tmp_b):    
    if tmp_a and tmp_b:
        a_enum_regex = _enumerate_regex(tmp_a)
        b_enum_regex = _enumerate_regex(tmp_b)
        if tmp_b in a_enum_regex: return tmp_a
        if tmp_a in b_enum_regex: return tmp_b

        if not _repeated_wrap(tmp_a): tmp_a = f"({tmp_a})"
        if not _repeated_wrap(tmp_b): tmp_b = f"({tmp_b})"
        return f"({tmp_a}|{tmp_b})"
        # return f"(({tmp_a})|({tmp_b}))"
    if tmp_a:
        return f"({tmp_a})?" if not _repeated_wrap(tmp_a) else tmp_a if tmp_a[-1] == "?" else f"{tmp_a}?"
    if tmp_b:
        return f"({tmp_b})?" if not _repeated_wrap(tmp_b) else tmp_b if tmp_b[-1] == "?" else f"{tmp_b}?"
    return ""

def _enumerate_regex(regex:str):
    enum_lst = []
    if not _repeated_wrap(regex):
        return enum_lst

    if regex.endswith(")"): 
        regex = regex[1:-1]
    elif regex.endswith(")?"): 
        regex = regex[1:-2]
        enum_lst.append("")

    op_stk = []
    vl_stk = []

    if regex[0] == "(": op_stk.append("(")
    i = 1
    tmp = ""
    while i < len(regex):
        cur = regex[i]
        pre = regex[i-1]
        if cur == "(" and pre != "\\":
            if op_stk and op_stk[-1] == "?":
                vl_stk = _enumerate_regex_helper(vl_stk, tmp)
                op_stk.pop()
            op_stk.append("(")
            tmp = ""
        elif cur == ")" and pre != "\\":
            op = op_stk.pop()
            if op == "?":
                vl_stk = _enumerate_regex_helper(vl_stk, tmp)
                op_stk.pop()
            elif op == "(":
                vl_stk.append(tmp)
            else:
                print("error")
            tmp = ""
        elif (cur == "|" and pre != "\\"):
            if op_stk and op_stk[-1] == "?":
                vl_stk = _enumerate_regex_helper(vl_stk, tmp)
                op_stk.pop()
            while vl_stk:
                enum_lst.append(vl_stk.pop())
        elif cur == "?" and pre == ")":
            op_stk.append("?")
        else:
            tmp += cur

        i += 1

    while vl_stk:
        enum_lst.append(vl_stk.pop())

    return enum_lst

def _enumerate_regex_helper(vl_stk:list, tmp):
    new_vl_lst = [] 
    if not vl_stk:
        new_vl_lst.append(tmp)
        new_vl_lst.append("")
        return new_vl_lst

    pre_regex = vl_stk.pop()
    append1 = pre_regex+tmp
    append2 = tmp
    if not vl_stk:
        new_vl_lst.append(append1)
        new_vl_lst.append(append2)
        
    while vl_stk:
        pre_regex = vl_stk.pop()
        new_vl_lst.append(pre_regex+append1)
        new_vl_lst.append(pre_regex+append2)  
    return new_vl_lst

def _repeated_wrap(regex):
    if regex[0] != "(": return False
    idx = parse_parenthesis(regex)
    if any([regex == items[2] for items in idx]):
        return True
    return False


def main():
    test = {
        "function(\\ [a-zA-Z_$][\\w$]*?)?\\([a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?\\)\\{var\\ [a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?;return\\ null==[a-zA-Z_$][\\w$]*?\\&\\&\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\),[a-zA-Z_$][\\w$]*?=\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\.match\\(/\\^\\[\\\\\\[\\\\\\]\\]\\*\\(\\[\\^\\\\\\[\\\\\\]\\]\\+\\)\\\\\\]\\*\\(\\.\\*\\)/\\)\\)\\[1\\]\\|\\|('|\")('|\"),('|\")('|\")===\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[2\\]\\|\\|('|\")('|\")\\)\\?[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]=[a-zA-Z_$][\\w$]*?:('|\")\\[\\]('|\")===[a-zA-Z_$][\\w$]*?\\?\\([a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\|\\|\\([a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]=\\[\\]\\),[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\.[a-zA-Z_$][\\w$]*?\\([a-zA-Z_$][\\w$]*?\\)\\):\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\.match\\(/\\^\\\\\\[\\\\\\]\\\\\\[\\(\\[\\^\\\\\\[\\\\\\]\\]\\+\\)\\\\\\]\\$/\\)\\|\\|[a-zA-Z_$][\\w$]*?\\.match\\(/\\^\\\\\\[\\\\\\]\\(\\.\\+\\)\\$/\\)\\)\\?\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[1\\],[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\|\\|\\([a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]=\\[\\]\\),null!=\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\[[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\.length\\-1\\]\\)\\&\\&[a-zA-Z_$][\\w$]*?\\.constructor===[a-zA-Z_$][\\w$]*?\\&\\&null": [
            "function(t,e,i){var s,n,o;return null==i&&(i=NULL),n=(o=e.match(/^[\\[\\]]*([^\\[\\]]+)\\]*(.*)/))[1]||\"\",\"\"===(s=o[2]||\"\")?t[n]=i:\"[]\"===s?(t[n]||(t[n]=[]),t[n].push(i)):(e=s.match(/^\\[\\]\\[([^\\[\\]]+)\\]$/)||s.match(/^\\[\\](.+)$/))?(o=e[1],t[n]||(t[n]=[]),null!=(e=t[n][t[n].length-1])&&e.constructor===Object&&null"
        ],
        "function(\\ [a-zA-Z_$][\\w$]*?)?\\([a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?\\)\\{var\\ [a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?;return\\ null==[a-zA-Z_$][\\w$]*?\\&\\&\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\),[a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\.match\\(/\\^\\[\\\\\\[\\\\\\]\\]\\*\\(\\[\\^\\\\\\[\\\\\\]\\]\\+\\)\\\\\\]\\*\\(\\.\\*\\)/\\),[a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[1\\]\\|\\|('|\")('|\"),[a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[2\\]\\|\\|('|\")('|\"),('|\")('|\")===[a-zA-Z_$][\\w$]*?\\?[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]=[a-zA-Z_$][\\w$]*?:('|\")\\[\\]('|\")===[a-zA-Z_$][\\w$]*?\\?\\([a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\|\\|\\([a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]=\\[\\]\\),[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\.[a-zA-Z_$][\\w$]*?\\([a-zA-Z_$][\\w$]*?\\)\\):\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\.match\\(/\\^\\\\\\[\\\\\\]\\\\\\[\\(\\[\\^\\\\\\[\\\\\\]\\]\\+\\)\\\\\\]\\$/\\)\\|\\|\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\.match\\(/\\^\\\\\\[\\\\\\]\\(\\.\\+\\)\\$/\\)\\)\\)\\?\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[1\\],[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\|\\|\\([a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]=\\[\\]\\),[a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\[[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\.length\\-1\\],null!=[a-zA-Z_$][\\w$]*?\\&\\&[a-zA-Z_$][\\w$]*?\\.constructor===": [
            "function(t,e,i){var n,o,s,a,r,l;return null==i&&(i=NULL),r=e.match(/^[\\[\\]]*([^\\[\\]]+)\\]*(.*)/),s=r[1]||\"\",n=r[2]||\"\",\"\"===n?t[s]=i:\"[]\"===n?(t[s]||(t[s]=[]),t[s].push(i)):(l=n.match(/^\\[\\]\\[([^\\[\\]]+)\\]$/)||(l=n.match(/^\\[\\](.+)$/)))?(o=l[1],t[s]||(t[s]=[]),a=t[s][t[s].length-1],null!=a&&a.constructor===Ob",
            "function(params,name,v){var after,child_key,k,lastP,result,result_i;return null==v&&(v=NULL),result=name.match(/^[\\[\\]]*([^\\[\\]]+)\\]*(.*)/),k=result[1]||\"\",after=result[2]||\"\",\"\"===after?params[k]=v:\"[]\"===after?(params[k]||(params[k]=[]),params[k].push(v)):(result_i=after.match(/^\\[\\]\\[([^\\[\\]]+)\\]$/)||(re"
        ],
        "function(\\ [a-zA-Z_$][\\w$]*?)?\\([a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?\\)\\{var\\ [a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?,[a-zA-Z_$][\\w$]*?;return\\ [a-zA-Z_$][\\w$]*?==null\\&\\&\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\),[a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\.match\\(/\\^\\[\\\\\\[\\\\\\]\\]\\*\\(\\[\\^\\\\\\[\\\\\\]\\]\\+\\)\\\\\\]\\*\\(\\.\\*\\)/\\),[a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[1\\]\\|\\|('|\")('|\"),[a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[2\\]\\|\\|('|\")('|\"),[a-zA-Z_$][\\w$]*?===('|\")('|\")\\?[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]=[a-zA-Z_$][\\w$]*?:[a-zA-Z_$][\\w$]*?===('|\")\\[\\]('|\")\\?\\([a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\|\\|\\([a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]=\\[\\]\\),[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\.[a-zA-Z_$][\\w$]*?\\([a-zA-Z_$][\\w$]*?\\)\\):\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\.match\\(/\\^\\\\\\[\\\\\\]\\\\\\[\\(\\[\\^\\\\\\[\\\\\\]\\]\\+\\)\\\\\\]\\$/\\)\\|\\|\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\.match\\(/\\^\\\\\\[\\\\\\]\\(\\.\\+\\)\\$/\\)\\)\\)\\?\\([a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[1\\],[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\|\\|\\([a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]=\\[\\]\\),[a-zA-Z_$][\\w$]*?=[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\[[a-zA-Z_$][\\w$]*?\\[[a-zA-Z_$][\\w$]*?\\]\\.length\\-1\\],[a-zA-Z_$][\\w$]*?!=null\\&\\&[a-zA-Z_$][\\w$]*?\\.constructor===": [
            "function(a,b,c){var d,e,f,g,h,i;return c==null&&(c=NULL),h=b.match(/^[\\[\\]]*([^\\[\\]]+)\\]*(.*)/),f=h[1]||\"\",d=h[2]||\"\",d===\"\"?a[f]=c:d===\"[]\"?(a[f]||(a[f]=[]),a[f].push(c)):(i=d.match(/^\\[\\]\\[([^\\[\\]]+)\\]$/)||(i=d.match(/^\\[\\](.+)$/)))?(e=i[1],a[f]||(a[f]=[]),g=a[f][a[f].length-1],g!=null&&g.constructor===Ob"
        ]
    }

    regexes = list(test.keys())
    merged = regexes.pop(0)
    lst = []
    for i, regex in enumerate(regexes):
        merged = merge_regex(merged, regex)
        lst.append(regex)
        if not all([any([re.search(merged, snippet) for snippet in test[regex_]]) for regex_ in lst]):
            print("error", i)
        else:
            print("pass", i)

    for j, regex_ in enumerate(lst):
        if not any([re.search(merged, snippet) for snippet in test[regex_]]):
            print("unmatched", j)
        else:
            print("match", j)


if __name__ == "__main__":
    main()