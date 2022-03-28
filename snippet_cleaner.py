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

def cleaner(snippet):
    snippet = comment_regex.sub("", snippet)
    # 1. convert hex char
    snippet = hexchar_regex.sub(lambda c: bytearray.fromhex(c.group(0)[-2:]).decode(), snippet)
    # 2. clean the space characters
    snippet = space_regex.sub("", snippet)
    # 3. clean the endmark
    snippet = endmark_regex.sub("", snippet)
    # 4. replace ' and "
    snippet = snippet.replace("\\\"", '"').replace("\\'", "'")
    # 5. escape characters in snippet, and escape the special character $, which is often used for defining a variable in js
    return snippet.replace("\$","$")
