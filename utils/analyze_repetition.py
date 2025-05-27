from typing import List, Dict, Tuple
import string
from collections import Counter

def tokenize(text: str) -> List[str]:
    """
    Cleans and tokenizes a transition phrase into individual words.
    Args:
        text (str): The input transition phrase
    Returns:
        List[str]: List of lowercase words, stripped of punctuation
    """
    
    # Remove punctuation and convert to lowercase
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translator).lower()
    
    # Split into words and filter out empty strings
    words = [word.strip() for word in cleaned_text.split()]
    return [word for word in words if word]

def analyze_transitions_batch(batch_outputs: List[List[str]]) -> Dict:
    """
    Analyzes a batch of transition outputs for word repetition patterns.
    Args:
        batch_outputs (List[List[str]]): List of transition phrase groups
    Returns:
        Dict: Analysis results including repetition statistics
    """
    all_repeated_words = Counter()
    details = []
    
    for output_id, transitions in enumerate(batch_outputs, 1):
        # Tokenize all words in this group
        all_words = []
        for transition in transitions:
            all_words.extend(tokenize(transition))
        
        # Count word frequencies in this group
        word_counts = Counter(all_words)
        
        # Find repeated words (frequency > 1)
        repeated_words = [word for word, count in word_counts.items() if count > 1]
        
        # Update global repeated words counter
        for word in repeated_words:
            all_repeated_words[word] += 1
        
        # Add details for this output
        details.append({
            "output_id": output_id,
            "transitions": transitions,
            "repeated_words": repeated_words,
            "repetition_count": len(repeated_words)
        })
    
    # Get most common repeated words across all outputs
    most_common = all_repeated_words.most_common()
    
    return {
        "total_outputs": len(batch_outputs),
        "outputs_with_repeats": sum(1 for d in details if d["repetition_count"] > 0),
        "most_common_repeated_words": most_common,
        "details": details
    }

# Example usage
if __name__ == "__main__":
    # Test data
    test_batch = [
        ["Par ailleurs,", "Toujours dans la région,", "Dans une autre affaire,"],
        ["Encore une fois,", "Dans le même temps,", "Encore dans le département voisin,"]
    ]
    
    # Run analysis
    results = analyze_transitions_batch(test_batch)
    
    # Print results
    print("Analysis Results:")
    print(f"Total outputs: {results['total_outputs']}")
    print(f"Outputs with repeats: {results['outputs_with_repeats']}")
    print("\nMost common repeated words:")
    for word, count in results['most_common_repeated_words']:
        print(f"- {word}: {count} times")
    
    print("\nDetailed analysis:")
    for detail in results['details']:
        print(f"\nOutput {detail['output_id']}:")
        print(f"Transitions: {detail['transitions']}")
        print(f"Repeated words: {detail['repeated_words']}")
        print(f"Repetition count: {detail['repetition_count']}") 