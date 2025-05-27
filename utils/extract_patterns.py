from collections import Counter
import re
from typing import List, Tuple
from utils.validate_prompt_compliance import tokenize, extract_ngrams
from utils.io import load_all_transitions  # to implement: returns List[List[str]]

MIN_COUNT = 3


def get_top_ngrams(dataset: List[List[str]], n: int, min_count: int = MIN_COUNT) -> List[Tuple[str, int]]:
    counter = Counter()
    for group in dataset:
        for phrase in group:
            words = tokenize(phrase)
            counter.update(extract_ngrams(words, n))
    return [(ng, count) for ng, count in counter.items() if count >= min_count]


def export_candidates_to_file(filename: str, bigrams: List[Tuple[str, int]], trigrams: List[Tuple[str, int]]):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("Top Bigrams:\n")
        for phrase, count in sorted(bigrams, key=lambda x: -x[1]):
            f.write(f"{phrase} ({count})\n")
        f.write("\nTop Trigrams:\n")
        for phrase, count in sorted(trigrams, key=lambda x: -x[1]):
            f.write(f"{phrase} ({count})\n")


def run_export():
    dataset = load_all_transitions()  # To be implemented in io.py
    bigrams = get_top_ngrams(dataset, n=2)
    trigrams = get_top_ngrams(dataset, n=3)
    export_candidates_to_file("candidates_for_gpt_review.txt", bigrams, trigrams) 