from typing import List, Dict, Set
import string
from collections import Counter
import os
import streamlit as st
import logging
from utils.logger import logger

def load_stopwords() -> Set[str]:
    stopwords_file = os.path.join(os.path.dirname(__file__), 'french_stopwords.txt')
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip()}

# Load French stopwords
FRENCH_STOPWORDS: Set[str] = load_stopwords()

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

def check_transition_group(transitions: List[str]) -> Dict:
    """
    Validates a group of transitions for repetition and 'enfin' placement.
    
    Args:
        transitions (List[str]): List of transition phrases
        
    Returns:
        Dict: Dictionary containing violation information
    """
    violations = {}
    
    # Check for word repetition (excluding stopwords)
    all_words = []
    for transition in transitions:
        words = tokenize(transition)
        # Filter out stopwords and empty strings
        meaningful_words = [w for w in words if w and w not in FRENCH_STOPWORDS]
        all_words.extend(meaningful_words)
    
    # Find repeated meaningful words
    word_counts = Counter(all_words)
    repeated_words = [word for word, count in word_counts.items() if count > 1]
    if repeated_words:
        violations["repetition"] = repeated_words
    
    # Check 'enfin' placement
    for i, transition in enumerate(transitions):
        words = tokenize(transition)
        if "enfin" in words and i != len(transitions) - 1:
            violations["enfin_misplaced"] = True
            break
    
    return violations

def validate_batch(batch_outputs: List[List[str]]) -> Dict:
    """
    Validates a batch of transition outputs for compliance with French transition rules.
    
    Args:
        batch_outputs (List[List[str]]): List of transition phrase groups
        
    Returns:
        Dict: Summary of violations and per-output breakdown
    """
    details = []
    repetition_violations = set()
    repetition_affected_outputs = set()
    enfin_misplaced_outputs = set()
    
    for output_id, transitions in enumerate(batch_outputs, 1):
        violations = check_transition_group(transitions)
        
        # Track violations for summary
        if "repetition" in violations:
            repetition_violations.update(violations["repetition"])
            repetition_affected_outputs.add(output_id)
        if violations.get("enfin_misplaced"):
            enfin_misplaced_outputs.add(output_id)
        
        # Add details for this output
        details.append({
            "output_id": output_id,
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
    logger.info(f"Affected Outputs: {results['violations_summary']['repetition']['affected_outputs']}")
    logger.info(f"Violated Words: {', '.join(results['violations_summary']['repetition']['violated_words'])}")
    
    logger.info("Enfin Misplacement:")
    logger.info(f"Count: {results['violations_summary']['enfin_misplaced']['count']}")
    logger.info(f"Affected Outputs: {results['violations_summary']['enfin_misplaced']['affected_outputs']}")
    
    logger.info("=== Detailed Analysis ===")
    for detail in results['details']:
        logger.info(f"Output {detail['output_id']}:")
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
        st.metric("Total Outputs", results['total_outputs'])
    with col2:
        st.metric("Outputs with Violations", results['outputs_with_violations'])
    
    # Violations Summary
    st.subheader("Violations Summary")
    
    # Repetition violations
    st.write("**Repetition Violations:**")
    rep_col1, rep_col2, rep_col3 = st.columns(3)
    with rep_col1:
        st.metric("Count", results['violations_summary']['repetition']['count'])
    with rep_col2:
        st.write("Affected Outputs:", results['violations_summary']['repetition']['affected_outputs'])
    with rep_col3:
        st.write("Violated Words:", ", ".join(results['violations_summary']['repetition']['violated_words']))
    
    # Enfin misplacement
    st.write("**Enfin Misplacement:**")
    enfin_col1, enfin_col2 = st.columns(2)
    with enfin_col1:
        st.metric("Count", results['violations_summary']['enfin_misplaced']['count'])
    with enfin_col2:
        st.write("Affected Outputs:", results['violations_summary']['enfin_misplaced']['affected_outputs'])
    
    # Detailed Analysis
    st.subheader("Detailed Analysis")
    for detail in results['details']:
        with st.expander(f"Output {detail['output_id']}"):
            st.write("**Transitions:**", detail['transitions'])
            if detail['violations']:
                st.write("**Violations:**", detail['violations'])
            else:
                st.success("No violations found")

if __name__ == "__main__":
    # Test data
    test_batch = [
        ["Par ailleurs,", "Par contre,", "Par exemple,"],
        ["Prenons la direction de Paris,", "Ensuite, prenons la direction de Lyon,", "Enfin, une note sur Marseille"],
        ["Enfin, une annonce importante", "Puis une autre nouvelle", "Pour conclure,"],
        ["Dans un autre registre,", "Dans la même région,", "Encore dans le domaine économique,"],
        ["À noter également,", "Nous terminons avec cette info :", "Pour finir,"]
    ]
    
    # Run validation
    results = validate_batch(test_batch)
    
    # Display results
    display_validation_results(results)