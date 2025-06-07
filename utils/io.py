# utils/io.py

import json
import os
from typing import List, Dict, Tuple
import streamlit as st
from utils.logger import logger

def load_examples() -> List[Dict]:
    """Load few-shot examples from transitions.json"""
    with open('transitions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_all_transitions() -> List[List[str]]:
    """
    Load all transitions from the corpus files.
    Returns a list of transition groups, where each group is a list of transitions.
    """
    transitions = []
    corpus_dir = os.path.join(os.path.dirname(__file__), '..', 'corpus')
    # Create corpus directory if it doesn't exist
    if not os.path.exists(corpus_dir):
        os.makedirs(corpus_dir)
        logger.info(f"Created corpus directory at {corpus_dir}")
        return []
    
    # Process each file in the corpus directory
    filepath = os.path.join(corpus_dir, 'corpus.txt')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        for line in content.split('\n'):
            transitions.append(line)

    except Exception as e:
        logger.error(f"Error processing corpus.txt: {str(e)}")
    return transitions