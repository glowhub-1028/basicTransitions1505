# utils/io.py

import json

def load_examples(file_path="transitions.json"):
    """
    Load full transition dataset: list of {input, transition} pairs.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
