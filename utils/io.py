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
    for filename in os.listdir(corpus_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(corpus_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract transitions section
                if "**Transitions générées:**" in content:
                    transitions_section = content.split("**Transitions générées:**")[1].strip()
                    # Parse numbered transitions
                    transition_group = []
                    for line in transitions_section.split('\n'):
                        if line.strip() and line[0].isdigit():
                            # Remove the number and dot prefix
                            transition = line.split('.', 1)[1].strip()
                            transition_group.append(transition)
                    if transition_group:
                        transitions.append(transition_group)
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
    
    return transitions