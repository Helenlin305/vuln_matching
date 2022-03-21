from extract_regex_v2 import CodeRegexExtractor
import json
import re
from collections import defaultdict

codeRegexExtractor = CodeRegexExtractor()
snippet_regex_dict = defaultdict(list)
dirty_data = []

def match_helper(vul_code):
    for code_regex in snippet_regex_dict:
        if re.search(code_regex, vul_code):
            snippet_regex_dict[code_regex].append(vul_code)
            return True
    return False

def handling(filename):
    with open(filename) as f:
        line = f.readline()
        raw_data = json.loads(line)

    print(len(raw_data))
    for elements in raw_data.values():
        vul_code = elements["vul_code"]
        if not vul_code or not vul_code.startswith("function"):
            dirty_data.append(vul_code)
            continue
        if match_helper(vul_code): continue
        snippet_regex = codeRegexExtractor.run(vul_code)
        snippet_regex_dict[snippet_regex].append(vul_code)

def get_statistics():
    statistics = defaultdict(int)
    for value in snippet_regex_dict.values():
        statistics[len(value)] += 1

    print("total snippet regex count: ", len(snippet_regex_dict))
    print(statistics)
    print(sorted(statistics.keys()))

    unique_statistics = defaultdict(int)
    for value in snippet_regex_dict.values():
        unique_statistics[len(set(value))] += 1
    print(unique_statistics)
    print(sorted(unique_statistics.keys()))

def output_result():
    with open("test_result.json", "w") as f:
        f.write(json.dumps(snippet_regex_dict))

    unique_dict = {key: list(set(value)) for key, value in snippet_regex_dict.items() if len(set(value))>1 }
    with open("test_result_unique.json", "w") as f:
        f.write(json.dumps(unique_dict))

    print(len(dirty_data))
    with open("dirty_data.txt", "w") as f:
        for line in set(dirty_data):
            if line:
                f.write(line+"\n")

def main():
    handling("web_report_new.json")
    handling("web_report.json")
    get_statistics()
    output_result()

if __name__ == "__main__":
    main()