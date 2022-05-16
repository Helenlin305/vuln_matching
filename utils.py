import re

endmark_list = [
    "\\n",
    "...\\n\" ) ),",
    "...\\n\\n"
]

endmark_regex = re.compile('|'.join([re.escape(i)+"$" for i in endmark_list]))
comment_regex = re.compile(r"//.*\\\\x0a|//.*\.\.\.\\n\\n|//.*\.\.\.\\n\" \) \),")
hexchar_regex = re.compile(r"\\\\x[0-9a-z]{2}")
space_regex   = re.compile(r"[\t\n\r\f\v]+| [ ]+")

string_regex = re.compile(r'((?<!\\)\'.*?(?<!\\)\'|(?<!\\)\".*?(?<!\\)\"|(?<!\\)`.*?(?<!\\)`|(?<!\\)/.*?(?<!\\)/[dgimsuy]?|(?:\'|"|\`|/).*\Z)')
clean_space_regex = re.compile(r"(. [^$\w]+ .?|[^$\w]+ .?|.? [^$\w]+)")

def _seconde_clean(snippet):
    strings = string_regex.findall(snippet)
    cleaned = ""
    for substr in string_regex.split(snippet):
        if substr in strings:
            cleaned += substr
            continue
        tmp = clean_space_regex.sub(lambda obj: obj.group(0).replace(" ", ''), substr)
        cleaned += tmp.replace(";}", "}")
        
    return cleaned


def cleaner(snippet):
    # 0. clean the comment
    snippet = comment_regex.sub("", snippet)
    # 1. convert hex char
    snippet = hexchar_regex.sub(lambda c: bytearray.fromhex(c.group(0)[-2:]).decode(), snippet)
    # 2. clean the repeated space characters
    snippet = space_regex.sub("", snippet)
    # 3. clean the endmark
    snippet = endmark_regex.sub("", snippet)
    # 4. replace ' and "
    snippet = snippet.replace("\\\"", '"').replace("\\'", "'")
    # 5. unescape "\\\\"
    snippet = snippet.replace("\\\\", "\\")
    # 6. clean the single space and semicolon before '}'
    snippet = _seconde_clean(snippet)
    return snippet

