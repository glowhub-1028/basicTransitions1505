import streamlit as st

def rebuild_article_with_transitions(user_input, transitions):
    """
    Rebuilds the article by inserting validated transitions between paragraph segments.

    Parameters:
    - user_input (str): The original article text with 'TRANSITION' markers.
    - transitions (list of str): List of transitions, one for each marker.

    Returns:
    - str: The reconstructed article with transitions inserted.
    - str or None: An error message if mismatch occurs, else None.
    """
    parts = user_input.split("TRANSITION")

    if len(parts) != len(transitions) + 1:
        return None, "Mismatch between number of TRANSITION markers and generated transitions."

    rebuilt_article = parts[0].strip()
    for i, t in enumerate(transitions):
        rebuilt_article += f"\n\n{t}\n\n{parts[i + 1].strip()}"

    return rebuilt_article, None
