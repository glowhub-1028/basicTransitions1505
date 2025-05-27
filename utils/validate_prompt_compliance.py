from typing import List, Dict, Set, Tuple
import string
from collections import Counter
import os
import streamlit as st
import re
from utils.logger import logger

def load_stopwords() -> Set[str]:
    stopwords_file = os.path.join(os.path.dirname(__file__), 'french_stopwords.txt')
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip()}

# Load French stopwords
FRENCH_STOPWORDS: Set[str] = load_stopwords()

def load_stylistic_expressions(filepath: str = 'stylistic_patterns.txt') -> Set[str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return {line.strip().lower() for line in f if line.strip()}

# Load stylistic patterns from file
STYLISTIC_EXPRESSIONS: Set[str] = load_stylistic_expressions()
print(STYLISTIC_EXPRESSIONS, "STYLISTIC_EXPRESSIONS🤞🤞🤞🤞")

def tokenize(text: str) -> List[str]:
    """
    Normalizes case, removes punctuation, and returns word tokens.
    
    Args:
        text (str): The input transition phrase 
        
    Returns:
        List[str]: List of lowercase words, stripped of punctuation
    """
    # Replace apostrophes with spaces to split words properly
    text = text.replace("'", " ")
    
    # Remove punctuation and convert to lowercase
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translator).lower()
    
    # Split into words and filter out empty strings
    words = [word.strip() for word in cleaned_text.split()]
    return [word for word in words if word]

def extract_ngrams(words: List[str], n: int) -> List[str]:
    """
    Extract n-grams from a list of words.
    
    Args:
        words (List[str]): List of words
        n (int): Size of n-gram
        
    Returns:
        List[str]: List of n-grams
    """
    return [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]

def check_stylistic_patterns(transitions: List[str]) -> List[str]:
    """
    Check for repetitive stylistic patterns in transitions.
    
    Args:
        transitions (List[str]): List of transition phrases
        
    Returns:
        List[str]: List of violated patterns
    """
    violations = []
    
    # Extract bigrams and trigrams from all transitions
    all_ngrams = []
    for transition in transitions:
        words = tokenize(transition)
        all_ngrams.extend(extract_ngrams(words, 2))  # bigrams
        all_ngrams.extend(extract_ngrams(words, 3))  # trigrams
    
    # Check for repeated stylistic expressions
    ngram_counts = Counter(all_ngrams)
    for expr in STYLISTIC_EXPRESSIONS:
        if ngram_counts[expr] > 1:
            violations.append(expr)
    
    return violations

def check_flexible_patterns(transitions: List[str]) -> List[str]:
    """
    Check for flexible pattern matches using regex.
    
    Args:
        transitions (List[str]): List of transition phrases
        
    Returns:
        List[str]: List of violated patterns
    """
    violations = []
    
    # Define flexible patterns
    patterns = [
        r'(sur|dans|par) un autre \w+',
        r'(sur|dans|par) la même \w+',
        r'(sur|dans|par) le même \w+',
        r'dans l\'actualité \w+',
        r'pour (terminer|conclure|finir)',
        r'(signalons|sachez|nous) \w+'
    ]
    
    # Check each transition against patterns
    for pattern in patterns:
        matches = []
        for transition in transitions:
            if re.search(pattern, transition.lower()):
                matches.append(transition)
        if len(matches) > 1:
            violations.append(pattern)
    
    return violations

def check_transition_group(transitions: List[str]) -> Dict:
    """
    Validates a group of transitions for repetition and 'enfin' placement.
    
    Args:
        transitions (List[str]): List of transition phrases
        
    Returns:
        Dict: Dictionary containing violation information
    """
    violations = {}
    
    # Check for word repetition at the beginning of phrases (including stopwords)
    first_words = []
    for transition in transitions:
        words = tokenize(transition)
        if words:  # If there are any words
            first_words.append(words[0])  # Get the first word
    
    # Find repeated first words
    first_word_counts = Counter(first_words)
    repeated_first_words = [word for word, count in first_word_counts.items() if count > 1]
    if repeated_first_words:
        violations["repetition"] = repeated_first_words
    
    # Check for content-bearing word repetition in mid-sentence (excluding stopwords)
    all_content_words = []
    for transition in transitions:
        words = tokenize(transition)
        if len(words) > 1:  # Only check mid-sentence words
            # Filter out stopwords and empty strings
            meaningful_words = [w for w in words[1:] if w and w not in FRENCH_STOPWORDS]
            all_content_words.extend(meaningful_words)
    
    # Find repeated content-bearing words
    content_word_counts = Counter(all_content_words)
    repeated_content_words = [word for word, count in content_word_counts.items() if count > 1]
    if repeated_content_words:
        if "repetition" in violations:
            violations["repetition"].extend(repeated_content_words)
        else:
            violations["repetition"] = repeated_content_words
    
    # Check for stylistic pattern repetition
    stylistic_violations = check_stylistic_patterns(transitions)
    if stylistic_violations:
        if "repetition" in violations:
            violations["repetition"].extend(stylistic_violations)
        else:
            violations["repetition"] = stylistic_violations
    
    # Check for flexible pattern matches
    flexible_violations = check_flexible_patterns(transitions)
    if flexible_violations:
        if "repetition" in violations:
            violations["repetition"].extend(flexible_violations)
        else:
            violations["repetition"] = flexible_violations
    
    # Check 'enfin' placement
    for i, transition in enumerate(transitions):
        words = tokenize(transition)
        if "enfin" in words and i != len(transitions) - 1:
            violations["enfin_misplaced"] = True
            break
    
    return violations

def validate_batch(batch_outputs: List[Tuple[str, List[str]]]) -> Dict:
    """
    Validates a batch of transition outputs for compliance with French transition rules.
    
    Args:
        batch_outputs (List[Tuple[str, List[str]]]): List of tuples containing (filename, transitions)
        
    Returns:
        Dict: Summary of violations and per-output breakdown
    """
    details = []
    repetition_violations = set()
    repetition_affected_outputs = set()
    enfin_misplaced_outputs = set()
    
    for filename, transitions in batch_outputs:
        violations = check_transition_group(transitions)
        
        # Track violations for summary
        if "repetition" in violations:
            repetition_violations.update(violations["repetition"])
            repetition_affected_outputs.add(filename)
        if violations.get("enfin_misplaced"):
            enfin_misplaced_outputs.add(filename)
        
        # Add details for this output
        details.append({
            "output_id": filename,
            "transitions": transitions,
            "violations": violations
        })
    
    # Calculate total violations
    total_violations = len(repetition_affected_outputs | enfin_misplaced_outputs)
    
    return {
        "total_outputs": len(batch_outputs),
        "outputs_with_violations": total_violations,
        "violations_summary": {
            "repetition": {
                "count": len(repetition_affected_outputs),
                "affected_outputs": sorted(list(repetition_affected_outputs)),
                "violated_words": sorted(list(repetition_violations))
            },
            "enfin_misplaced": {
                "count": len(enfin_misplaced_outputs),
                "affected_outputs": sorted(list(enfin_misplaced_outputs))
            }
        },
        "details": details
    }

def display_validation_results(results):
    """
    Display validation results using Streamlit components in a clean, organized format.
    Also prints results to console.
    """
    # Log to console
    logger.info("=== Validation Results ===")
    logger.info(f"Total Outputs: {results['total_outputs']}")
    logger.info(f"Outputs with Violations: {results['outputs_with_violations']}")
    
    logger.info("=== Violations Summary ===")
    logger.info("Repetition Violations:")
    logger.info(f"Count: {results['violations_summary']['repetition']['count']}")
    logger.info(f"Affected Files: {results['violations_summary']['repetition']['affected_outputs']}")
    logger.info(f"Violated Words: {', '.join(results['violations_summary']['repetition']['violated_words'])}")
    
    logger.info("Enfin Misplacement:")
    logger.info(f"Count: {results['violations_summary']['enfin_misplaced']['count']}")
    logger.info(f"Affected Files: {results['violations_summary']['enfin_misplaced']['affected_outputs']}")
    
    logger.info("=== Detailed Analysis ===")
    for detail in results['details']:
        logger.info(f"File: {detail['output_id']}")
        logger.info(f"Transitions: {detail['transitions']}")
        if detail['violations']:
            logger.info(f"Violations: {detail['violations']}")
        else:
            logger.info("No violations found")

    # Display in Streamlit UI
    st.subheader("Validation Results")
    
    # Overall statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Files", results['total_outputs'])
    with col2:
        st.metric("Files with Violations", results['outputs_with_violations'])
    
    # Violations Summary
    st.subheader("Violations Summary")
    
    # Repetition violations
    st.write("**Repetition Violations:**")
    rep_col1, rep_col2, rep_col3 = st.columns(3)
    with rep_col1:
        st.metric("Count", results['violations_summary']['repetition']['count'])
    with rep_col2:
        st.write("Affected Files:", results['violations_summary']['repetition']['affected_outputs'])
    with rep_col3:
        st.write("Violated Words:", ", ".join(results['violations_summary']['repetition']['violated_words']))
    
    # Enfin misplacement
    st.write("**Enfin Misplacement:**")
    enfin_col1, enfin_col2 = st.columns(2)
    with enfin_col1:
        st.metric("Count", results['violations_summary']['enfin_misplaced']['count'])
    with enfin_col2:
        st.write("Affected Files:", results['violations_summary']['enfin_misplaced']['affected_outputs'])
    
    # Detailed Analysis
    st.subheader("Detailed Analysis")
    for detail in results['details']:
        with st.expander(f"File: {detail['output_id']}"):
            st.write("**Transitions:**", detail['transitions'])
            if detail['violations']:
                st.write("**Violations:**", detail['violations'])
            else:
                st.success("No violations found")

if __name__ == "__main__":
    # Test data with file names
    test_batch = [
        ("article_20250525_013229.txt", ["Par ailleurs,", "Par contre,", "Par exemple,"]),
        ("article_20250524_191814.txt", ["Prenons la direction de Paris,", "Ensuite, prenons la direction de Lyon,", "Enfin, une note sur Marseille"]),
        ("article_20250524_191815.txt", ["Enfin, une annonce importante", "Puis une autre nouvelle", "Pour conclure,"]),
        ("article_20250524_191816.txt", ["Dans un autre registre,", "Dans la même région,", "Encore dans le domaine économique,"]),
        ("article_20250524_191817.txt", ["À noter également,", "Nous terminons avec cette info :", "Pour finir,"])
    ]
    
    # Run validation
    results = validate_batch(test_batch)
    
    # Display results
    display_validation_results(results)