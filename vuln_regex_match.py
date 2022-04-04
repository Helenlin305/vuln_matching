from extract_regex_v2 import CodeRegexExtractor
from utils import cleaner
from collections import defaultdict
import json
import logging
import re

logger = logging.getLogger()

class VulRegexMatcher(object):

    def __init__(self):
        self.cre = CodeRegexExtractor()
        self.vul_regex_set = defaultdict(set)
        self.vul_splitted_regex_set = defaultdict(set)
        self.vul_matched_result = defaultdict(list)

    def initialize_dataset(self, filename):
        with open(filename, 'r') as f:
            line = f.readline()
            raw_data = json.loads(line)

        logger.info("Begin initializing %s with %s snippets...", filename, len(raw_data))

        counter = 0
        for elements in raw_data.values():
            vul_code = elements["vul_code"]
            if not vul_code or not vul_code.startswith("function"):
                continue
            if self.check_exist(vul_code): 
                continue
            snippet_regex = self.cre.run(vul_code)
            if not snippet_regex:
                continue
            if self.check_sub_exist(snippet_regex, vul_code):
                continue
            self.vul_regex_set[snippet_regex].add(vul_code)
            counter += 1

        logger.info("Finished processing %s and added %s pieces of regex.", filename, counter)

    def initialize_fuzzy_dataset(self, filename):
        with open(filename, 'r') as f:
            line = f.readline()
            raw_data = json.loads(line)

        logger.info("Begin initializing %s with %s snippets...", filename, len(raw_data))

        counter = 0
        for elements in raw_data.values():
            vul_code = elements["vul_code"]
            if not vul_code or not vul_code.startswith("function"):
                continue
            if self.check_fuzzy_exist(vul_code): 
                continue
            snippet_regex = self.cre.run(vul_code)
            if not snippet_regex:
                continue            
            if self.check_sub_fuzzy_exist(snippet_regex, vul_code):
                continue
            self.vul_splitted_regex_set[snippet_regex].add(vul_code)
            counter += 1

        logger.info("Finished processing %s and added %s pieces of regex.", filename, counter)

    def load_dataset(self, filename, fuzzy=False):
        with open(filename, 'r') as f:
            line = f.readline()
            raw_data = json.loads(line.strip())
        if not fuzzy:
            for k, v in raw_data:
                self.vul_regex_set[k] = v
        else:
            for k, v in raw_data:
                self.vul_splitted_regex_set[k] = v

    def dump_dataset(self, filename, fuzzy=False):
        logger.info("Dump dataset into %s", filename)
        dataset = self.vul_regex_set if not fuzzy else self.vul_splitted_regex_set
        with open(filename, 'w') as f:
            tmp = {k: list(v) for k, v in dataset.items()}
            line = json.dumps(tmp)
            f.write(line)

    def process(self, codes):
        for code in codes:
            self.match(code)

    def dump_matched_result(self, filename):
        logger.info("Dump result into %s", filename)
        with open(filename, 'w') as f:
            line = json.dumps(self.vul_matched_result)
            f.write(line)

    def check_exist(self, vul_code):
        cleaned = cleaner(vul_code)
        for code_regex in self.vul_regex_set:
            if re.search(code_regex, cleaned):
                self.vul_regex_set[code_regex].add(vul_code)
                return True
        return False

    def check_fuzzy_exist(self, vul_code):
        cleaned = cleaner(vul_code)
        for splitted_regex in self.vul_splitted_regex_set:
            matched_counter = [re.search(stmt_regex, cleaned) for stmt_regex in splitted_regex.split(";")]
            if matched_counter.count(None) <= 3 and len(matched_counter) >= 5:
                self.vul_splitted_regex_set[splitted_regex].add(vul_code)
                return True
        return False

    def check_sub_exist(self, snippet_regex, vul_code):
        for code_regex in self.vul_regex_set:
            if snippet_regex in code_regex:
                self.vul_regex_set[code_regex].add(vul_code)
                return True
        return False

    def check_sub_fuzzy_exist(self, snippet_regex, vul_code):
        if self.check_sub_exist(snippet_regex, vul_code): 
            return True
        splitted = set(snippet_regex.split(";"))
        for splitted_regex in self.vul_splitted_regex_set:
            tmp = set(splitted_regex.split(";"))
            if splitted < tmp \
                or (len(splitted) > 2 and len(splitted - tmp) <= 1):
                self.vul_splitted_regex_set[splitted_regex].add(vul_code)
                return True
        return False

    def match(self, code):
        cleaned = cleaner(code)
        for code_regex in self.vul_regex_set:
            if re.search(code_regex, cleaned):
                self.vul_matched_result[code_regex].append(code)
                return True
        return False

    def fuzzy_match(self, code):
        cleaned = cleaner(code)
        for splitted_regex in self.vul_splitted_regex_set:
            matched_counter = [re.search(stmt_regex, cleaned) for stmt_regex in splitted_regex]
            if matched_counter.count(False) <= 1 and matched_counter.count(True) > 1:
                self.vul_matched_result[splitted_regex].append(code)
                return True
        return False



def test():
    vrm = VulRegexMatcher()
    # vrm.initialize_dataset("web_report_new.json")
    # vrm.initialize_dataset("web_report.json")
    # vrm.dump_dataset("vul_regex.json")

    # vrm.initialize_fuzzy_dataset("web_report_new.json")
    # vrm.initialize_fuzzy_dataset("web_report.json")
    # vrm.dump_dataset("vul_regex_splitted.json", fuzzy=True)

    vrm.initialize_fuzzy_dataset("test.json")
    vrm.dump_dataset("vul_regex_splitted.json", fuzzy=True)


if __name__ == "__main__":
    test()