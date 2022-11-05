# vuln_matching
### Background

---

```python
"function o(t,e,r,n){var i=t.shift();if(i){var f=e[r]=e[r]||[];"
"function c(e,t,n,r){var i=e.shift();if(i){var s=t[n]=t[n]||[];"
```

- We have collected many vulnerable js code snippets by *ProbeTheProto*, many of them are similar:
    - Only the variable names are different;
    - Or the order of the statements is different.
- Therefore, we want to use these known vulnerable js code snippets to find more similar js codes in real world which cannot be detected by *ProbeTheProto.*
- Solution:
    - Extract the regex (regular expression) of the code snippet and use them to match the js code file.
        - Only replace all variables by the variable regex `[a-zA-Z_$][\w$]*?` , and keep the rest of the code structure.
        - Use exact match function `re.search` to match.
    - Compressing the regex dataset by merging multiple similar regular expressions into a super regex, if the similarity reaches the set threshold.

### Have Done

---

1. String preprocessing: clean the comments, convert hex chars, etc.
2. Extract the regex for code snippets, it can merge the sub-regex.
3. Compress regex: if multiple regular expressions are similar, merge them to generate a super regex.

### Code Structure

---

- `vuln_regex_match.py`
    - `class VulnRegexMatcher()`
        - This class contains all methods of extracting regex and matching.
    - `classmethod initialize_dataset(filename, dedup=True, clean=True)`
        - Load code snippets from file `filename` and extract corresponding regex to initialize dataset `self.vul_regex_set` which is a key-value pair: key is regex and value is a list which contains all code snippets from which the corresponding regex is extracted.
        - `dedup` is `True` when you want to remove duplicate code snippets. `clean` is `True` when you want to save the cleaned code snippets (e.g., remove comment).
        - The file format is same as the provided file `web_report_new` and `web_report` in *json* format.
        - Input file example: `web_report_new.json` and `web_report.json` .
    - `classmethod load_dataset(filename)`
        - Load regexes and code snippets from file `filename` to `self.vul_regex_set` .
    - `classmethod load_compressed_dataset(filename)`
        - Load compressed regexes and code snippets from file `filename` to `self.compressed_regex_set` .
    - `classmethod dump_dataset(filename, dedup=True, clean=True)`
        - Dump extracted regexes and original code snippets to file `filename`.
        - The output file is also *json* format with key-value pairs. Key is regex and value is a list which contains all code snippets from which the corresponding regex is extracted.
        - `dedup` is `True` when you want to remove duplicate code snippets. `clean` is `True` when you want to output the cleaned code snippets (e.g., remove comment).
        - Output file example: `vul_regex.json` and `vul_regex_clean.json` .
    - `classmethod dump_compressed_dataset(filename)`
        - Dump compressed regexes, original regexes and code snippets to file `filename`.
        - The output file is also *json* format with key-value pairs. Key is merged regex and value is also a key-value pair: key is original regexes and value is a list which contains all code snippets from which the corresponding regex is extracted.
        - Output file example: `compressed_regex.json` .
    - `classmethod compress_regex_dataset(threshold=0.85)`
        - Compress the regex dataset `self.vul_regex_set` to compressed regex dataset `self.compress_regex_set` by merging similar regexes into a super regex.
        - `threshold` is the similarity threshold. The similarity score is calculated by `[difflib.SequenceMatcher.ratio()](https://docs.python.org/3.10/library/difflib.html#difflib.SequenceMatcher.ratio)` . The default threshold is `0.85` .
        - The merged idea is to find a similar group and extract super regex based on the regexes in the group. For any regex, it iterates though each group, then iterates through each regexes in the group to calculate the similarity score, and once the similarity score with any regex in the group exceeds the set threshold, it will be grouped into that group, and then the new super regex for that group will be extracted.
    - `classmethod process(compress=True)`
        - Try to use the regex dataset to match the js codes. The codes should be loaded first by `load_query_dataset` .
        - `compress` is `True` when you want to use `self.compress_regex_set` to match.
    - `classmethod load_query_dataset(filename)`
        - Load js codes to be queried. The format is a string list in json format.
        - Input file example: `query_set.json` .
    - `classmethod dump_matched_result(filename)`
        - Dump the matched result to file `filename` . The output format is in json format with key-value pair. Key is hit regex and value is a list which contains the matched js code.
        - Output file example: `matched_result.json` .
    - `classmethod show_matched_result()`
        - Print matched result.
    - `classmethod show_statistics(compress=False)`
        - Print dataset statistics.
- `extract_regex_v2.py`
    - `class CodeRegexExtractor()`
        - This class is used for extracting regex of code snippet
    - `classmethod run(snippet)`
        - Return the corresponding regex of `snippet`
    - `classmethod clean(snippet)`
        - Clean snippet, e.g., remove comment, convert hex chars, etc.
- `regex_diff.py`
    - `function is_similar(a, b, threshold=0.85, strict=True)`
        - Determine if two strings `a` and `b` are similar. Return `Ture` when the score calculated by `[difflib.SequenceMatcher.ratio()](https://docs.python.org/3.10/library/difflib.html#difflib.SequenceMatcher.ratio)` exceeds the set threshold.
        - `strict` is `Ture` when you want to use strict mode. Use whole strings to calculate score and both strings must be longer than a certain value.
    - `function merge_regex(a, b)`
        - Merge two regexes into a super regex.
        - The first step is to parse regexes and identify the regex substring which shouldn’t be split when merging. Next step is to get the matching blocks. The last step is to merge two regexes based on previous results.
- `utils.py`
    - `function cleaner(snippet)`
        - Clean the snippet, e.g., remove comment, convert hex char. Used to pre-processing queried strings before matching.
