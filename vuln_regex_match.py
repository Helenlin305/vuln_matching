from extract_regex_v2 import CodeRegexExtractor
from regex_diff import merge_regex, is_similar
from utils import cleaner
from collections import defaultdict
import json
import logging
import re

msgfmt = "%(asctime)s [%(filename)s|%(funcName)s|:%(lineno)s] %(levelname)s: %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"
fmtter = logging.Formatter(fmt=msgfmt, datefmt=datefmt)
handler = logging.StreamHandler()
# handler = logging.FileHandler("../log/%s.log"%args.date)
handler.setFormatter(fmtter)
logging.getLogger().addHandler(handler)
logging.root.setLevel(logging.INFO)
logger = logging.getLogger("vulnregexmatch")

class VulnRegexMatcher(object):

    def __init__(self):
        self.cre = CodeRegexExtractor()
        self.vul_regex_set = defaultdict(list)
        self.vul_matched_result = defaultdict(list)
        self.compress_regex_set = defaultdict(dict)
        self.query_set = []

    def initialize_dataset(self, filename, dedup=True, clean=True):
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
            self.vul_regex_set[snippet_regex].append(vul_code)
            counter += 1

        if dedup:
            for k, v in self.vul_regex_set.items():
                self.vul_regex_set[k] = list(set(v))
        if clean:
            for k, v in self.vul_regex_set.items():
                self.vul_regex_set[k] = list(map(cleaner, v))

        logger.info("Finished processing %s and added %s pieces of regex.", filename, counter)

    def load_dataset(self, filename):
        with open(filename, 'r') as f:
            line = f.readline()
            raw_data = json.loads(line.strip())

        for k, v in raw_data:
            self.vul_regex_set[k].extend(v)

    def load_compressed_dataset(self, filename):
        with open(filename, 'r') as f:
            line = f.readline()
            raw_data = json.loads(line.strip())

        for k, v in raw_data:
            self.compress_regex_set[k].update(v)


    def dump_dataset(self, filename, dedup=True, clean=True):
        logger.info("Dump dataset into %s", filename)
        target = self.vul_regex_set
        dataset = {k: set(v) for k, v in target.items()} if dedup else target
        tmp = {k: list(v) for k, v in dataset.items()} if not clean else {k: list(map(cleaner, v)) for k, v in dataset.items()}
        with open(filename, 'w') as f:
            line = json.dumps(tmp)
            f.write(line)

    def dump_compressed_dataset(self, filename):
        logger.info("Dump compressed dataset into %s", filename)
        target = self.compress_regex_set        
        compress_regexes = dict(sorted(target.items(), key=lambda item: len(item[1]), reverse=True))
        with open(filename, 'w') as f:
            line = json.dumps(compress_regexes)
            f.write(line)

    def check_exist(self, vul_code):
        cleaned = cleaner(vul_code)
        for code_regex in self.vul_regex_set:
            if re.search(code_regex, cleaned):
                self.vul_regex_set[code_regex].append(vul_code)
                return True
        return False

    def check_sub_exist(self, snippet_regex, vul_code):
        for code_regex in self.vul_regex_set:
            if snippet_regex in code_regex:
                self.vul_regex_set[code_regex].append(vul_code)
                return True
            if code_regex in snippet_regex:
                self.vul_regex_set[snippet_regex] = self.vul_regex_set.pop(code_regex)
                self.vul_regex_set[snippet_regex].append(vul_code)
                return True
        return False

    def compress_regex_dataset(self, threshold=0.85):
        logger.info("Begin compressing %s regexes...", len(self.vul_regex_set))

        compress_regexes = defaultdict(dict)

        for regex, strings in self.vul_regex_set.items():
            flag = False
            for merged, regex_lst in compress_regexes.items():
                if any([is_similar(tmp_regex, regex, threshold=threshold) for tmp_regex in regex_lst]):
                    new_merged = merge_regex(merged, regex)
                    regex_lst[regex] = strings
                    compress_regexes[new_merged] = regex_lst
                    compress_regexes.pop(merged)
                    flag = True
                    break
            if not flag:
                compress_regexes[regex] = {regex: strings}

        self.compress_regex_set = compress_regexes

        logger.info("Finished compressing regexes to %s pieces.", len(compress_regexes))

    def process(self, compress=True):
        logger.info("Begin processing %s queries...", len(self.query_set))

        for code in self.query_set:
            self.match(code, compress)

        logger.info("Finished processing %s queries.", len(self.query_set))

    def match(self, code, compress=True):
        regex_set = self.compress_regex_set if compress else self.vul_regex_set
        cleaned = cleaner(code)
        for code_regex in regex_set:
            if re.search(code_regex, cleaned):
                self.vul_matched_result[code_regex].append(code)
                return True
        return False

    def load_query_dataset(self, filename):
        logger.info("Load query dataset from %s", filename)
        with open(filename, 'r') as f:
            line = f.readline()
            raw_data = json.loads(line.strip())
        
        self.query_set.extend(raw_data)

    def dump_matched_result(self, filename):
        logger.info("Dump matched result into %s", filename)
        with open(filename, 'w') as f:
            line = json.dumps(self.vul_matched_result)
            f.write(line)

    def show_matched_result(self):
        print("=============Matched Result=============")
        print(f"Total query: {len(self.query_set)}")
        matched_count = sum([len(item) for item in self.vul_matched_result.values()])
        print(f"Match count: {matched_count}")
        print(f"Hit regexes: {len(self.vul_matched_result)}")

    def show_statistics(self, compress=False):
        target = self.compress_regex_set if compress else self.vul_regex_set
        print("===============Statistics===============")
        print(f"Total  count: {len(target)}")
        statistics = defaultdict(int)
        for value in target.values():
            statistics[len(value)] += 1
        print(f"Single count: {statistics.pop(1)}")
        print(f"Other  count: {dict(statistics)}")


def main():
    vrm = VulnRegexMatcher()

    vrm.initialize_dataset("./input/web_report_new.json")
    vrm.initialize_dataset("./input/web_report.json")
    vrm.dump_dataset("./output/vul_regex.json")
    vrm.dump_dataset("./output/vul_regex_clean.json", clean=True)
    vrm.show_statistics()

    vrm.compress_regex_dataset()
    vrm.dump_compressed_dataset("./output/compressed_regex.json")
    vrm.show_statistics(compress=True)

    vrm.load_query_dataset("./input/query_set.json")
    vrm.process()
    vrm.dump_matched_result("./output/matched_result.json")
    vrm.show_matched_result()


if __name__ == "__main__":
    main()