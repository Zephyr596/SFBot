"""
Usage:
   python make_table.py <input_dir>
"""

import logging
from pytablewriter import MarkdownTableWriter, LatexTableWriter
import os
import json
import sys
import csv
import datetime


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_table(result_dict):
    """Generate table of results."""
    md_writer = MarkdownTableWriter()
    latex_writer = LatexTableWriter()
    md_writer.headers =  ["Model", "Precision", "ppl_result"]
    latex_writer.headers = ["Model", "Precision", "ppl_result"]

    languages = ["en", "zh"]
    values = []
    for model, model_results in result_dict.items():
        for precision, prec_results in model_results.items():
            value = [model, precision]
            for language in languages:
                task_results = prec_results.get(language, None)
                if task_results is None:
                    continue
                else:
                    result = task_results["results"]
                    value.append("%.4f" % result)
            values.append(value)
            model = ""    
            precision = ""
        
    md_writer.value_matrix = values
    latex_writer.value_matrix = values

    # todo: make latex table look good
    # print(latex_writer.dumps())

    return md_writer.dumps()


def merge_results(path):
    # loop dirs and subdirs in results dir
    # for each dir, load json files
    print('Read from', path)
    merged_results = dict()
    for dirpath, dirnames, filenames in os.walk(path):
        # skip dirs without files
        if not filenames:
            continue
        for filename in sorted([f for f in filenames if f.endswith("result.json")]):
            path = os.path.join(dirpath, filename)
            model, device, precision, language = dirpath.split('/')[-4:]
            with open(path, "r") as f:
                result_dict = json.load(f)
            if model not in merged_results:
                merged_results[model] = dict()
            if precision not in merged_results[model]:
                merged_results[model][precision] = dict()
            merged_results[model][precision][language] = result_dict
    return merged_results


def main(*args):
    if len(args) > 1:
        input_path = args[1]
    else:
        raise ValueError("Input path is required")

    merged_results = merge_results(input_path)
    print(make_table(merged_results))


if __name__ == "__main__":
    # when running from the harness, the first argument is the script name
    # you must name the second argument and the third argument(optional) to be the input_dir and output_dir
    main(*sys.argv)