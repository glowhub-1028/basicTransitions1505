import os
from collections import Counter
from utils.io import load_all_transitions
from utils.validate_prompt_compliance import tokenize, extract_ngrams, load_stylistic_expressions

TRANSITIONS_FILE = 'transitions.json'
STYLISTIC_FILE = 'stylistic_patterns.txt'

def run_full_debug():
    report = []

    # Step 0: Check file presence
    report.append("📁 Verifying required files...")
    if not os.path.exists(TRANSITIONS_FILE):
        report.append(f"❌ Missing required file: {TRANSITIONS_FILE}")
        return report
    if not os.path.exists(STYLISTIC_FILE):
        report.append(f"❌ Missing required file: {STYLISTIC_FILE}")
        return report
    report.append("✅ Required files found.")

    # Step 1: Load transitions
    report.append("🔍 Loading transitions...")
    data = load_all_transitions()
    
    if not isinstance(data, list):
        report.append("❌ Transitions format invalid.")
        return report

    report.append("✅ Transitions loaded successfully.")
    report.append(f"📦 Total Transitions: {len(data)}")
    report.append("📦 Sample output (first 2 Transition):")
    for i, group in enumerate(data[:2]):
        report.append(f"Transition {i + 1}: {group}")

    # Step 2: Check for duplicates
    all_phrases = [phrase.strip().lower() for phrase in data]
    phrase_counts = Counter(all_phrases)
    
    duplicates = {phrase: count for phrase, count in phrase_counts.items() if count > 1}

    if duplicates:
        report.append("\n⚠️ Duplicate transitions found:")
        for phrase, count in sorted(duplicates.items(), key=lambda x: -x[1]):
            report.append(f"  {phrase} ({count} times)")
    else:
        report.append("\n✅ No duplicate transitions detected.")

    # Step 3: N-gram analysis
    report.append("\n🧮 Analyzing common bigrams and trigrams...")
    all_ngrams = []
    for phrase in data:
        all_ngrams.extend(extract_ngrams(tokenize(phrase), 2))
        all_ngrams.extend(extract_ngrams(tokenize(phrase), 3))

    ngram_counts = Counter(all_ngrams)
    common_ngrams = [(ng, c) for ng, c in ngram_counts.items() if c >= 3]
    if common_ngrams:
        report.append("🔢 Frequent stylistic n-grams (count ≥ 3):")
        for ngram, count in sorted(common_ngrams, key=lambda x: -x[1])[:20]:
            report.append(f"  {' '.join(ngram)} ({count} times)")
    else:
        report.append("✅ No repeated n-grams found above threshold.")

    # Step 4: Stylistic validation
    report.append("\n📝 Validating transitions against stylistic_patterns.txt...")
    stylistic_patterns = load_stylistic_expressions()
    found = []
    not_found = []

    for phrase in all_phrases:
        if phrase in stylistic_patterns:
            found.append(phrase)
        else:
            not_found.append(phrase)

    report.append(f"✅ {len(found)} transitions match known stylistic patterns.")
    report.append(f"❓ {len(not_found)} transitions NOT found in stylistic_patterns.txt (review needed).")

    if not_found:
        report.append("\n📄 Sample of unmatched transitions:")
        for phrase in sorted(set(not_found))[:10]:
            report.append(f"  {phrase}")

    return report

if __name__ == "__main__":
    report = run_full_debug()
    print("\n".join(report))
