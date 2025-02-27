#!/usr/bin/env python3
import os
import sys
import json
import time
import math

def get_file_path(filename):
    """Return the absolute path if the file exists in cwd or script directory."""
    if os.path.exists(filename):
        return os.path.abspath(filename)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, filename)
    if os.path.exists(candidate):
        return candidate
    return None

def load_data(json_filename):
    """Load the associative JSON data."""
    path = get_file_path(json_filename)
    if not path:
        sys.exit(f"Error: {json_filename} not found.")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "words" in data and "mappings" in data:
                return data
            else:
                sys.exit("Invalid JSON structure.")
    except Exception as e:
        sys.exit(f"Failed to load JSON: {e}")

def softmax_dict(d):
    """Compute a softmax normalization on dictionary values."""
    if not d:
        return {}
    values = list(d.values())
    max_val = max(values)
    exp_values = {k: math.exp(v - max_val) for k, v in d.items()}
    sum_exp = sum(exp_values.values())
    return {k: exp_val / sum_exp for k, exp_val in exp_values.items()}

def get_word_object_by_id(data, word_id):
    """Return the word object from data whose id equals word_id."""
    for w in data["words"]:
        if w["id"] == int(word_id):
            return w
    return None

def get_right_associations_at_offset(word_obj, offset, max_count=-1):
    """
    Return the right associations dictionary for a given offset (as string) from the word object.
    Optionally, limit to the top max_count associations by raw count.
    """
    assoc = word_obj.get("R", {}).get(str(offset), {})
    if max_count != -1:
        sorted_keys = sorted(assoc, key=lambda k: assoc[k], reverse=True)[:max_count]
        return {k: assoc[k] for k in sorted_keys}
    return assoc

def generate_next_word(current_tokens, data, context_depth, discount_factor):
    """
    Predict the next word using the new JSON format.
    For each of the last up-to 'context_depth' tokens in current_tokens,
    use its right associations at the offset corresponding to its position
    (last token offset=1, second-last offset=2, etc.). Each association dictionary is softmax–normalized.
    Additionally, if a candidate appears already in the current sentence, discount its score
    based on its distance from the end.
    Frequency normalization is applied by dividing by log(seen+1).
    Returns the candidate word with the highest aggregated score.
    """
    mappings = data["mappings"]
    word_to_id = mappings["word_to_id"]
    id_to_word = mappings["id_to_word"]

    candidate_scores = {}  # key: candidate word id (as str), value: aggregated score

    # Determine left context (the whole current sentence)
    left_context = current_tokens

    # For each of the last tokens up to context_depth:
    num_tokens = len(current_tokens)
    for pos in range(1, min(context_depth, num_tokens) + 1):
        token = current_tokens[-pos]
        if token not in word_to_id:
            continue
        word_id = str(word_to_id[token])
        word_obj = get_word_object_by_id(data, word_id)
        if not word_obj:
            continue
        # Get right associations at offset = pos (as a string key)
        assoc_raw = get_right_associations_at_offset(word_obj, pos, max_count=-1)
        assoc_normalized = softmax_dict(assoc_raw)
        for assoc_id, prob in assoc_normalized.items():
            candidate_word = id_to_word.get(assoc_id)
            # Discount if candidate already appears in left_context (choose closest distance)
            discount = 1.0
            for idx in range(len(left_context)-1, -1, -1):
                if left_context[idx] == candidate_word:
                    distance = len(left_context) - idx  # 1-based distance
                    discount = distance * discount_factor
                    break
            # Base score from this token
            score = prob / discount
            # Further normalize by candidate frequency:
            candidate_obj = get_word_object_by_id(data, assoc_id)
            if candidate_obj:
                seen = candidate_obj.get("seen", 1)
                freq_norm = math.log(seen + 1)
            else:
                freq_norm = 1.0
            final_score = score / freq_norm
            candidate_scores[assoc_id] = candidate_scores.get(assoc_id, 0) + final_score

    if not candidate_scores:
        return None
    best_assoc_id, best_score = max(candidate_scores.items(), key=lambda x: x[1])
    return id_to_word.get(best_assoc_id)

def generate_text(data, initial_sentence, num_words, context_depth, discount_factor):
    """
    Generate text word by word. At each step the generator uses the new
    JSON associative data and the current sentence's last context_depth words
    (using positional right associations) to predict the next word.
    Only the newly generated word is printed.
    Returns the full generated sentence as a list of tokens.
    """
    current_tokens = initial_sentence.split()
    for i in range(num_words):
        next_word = generate_next_word(current_tokens, data, context_depth, discount_factor)
        if not next_word:
            print("\nNo candidate next word found. Stopping generation.")
            break
        print(next_word)  # print only the new word
        current_tokens.append(next_word)
        # (Optional) slight pause for real-time effect:
        time.sleep(0.2)
    return current_tokens

def main():
    # File names.
    json_filename = "offset_position_associative_data.json"
    # (Assumes that the builder script has already created this file.)
    data = load_data(json_filename)

    # Ask user for parameters—with defaults if nothing entered.
    try:
        context_depth = int(input("Enter context depth for generation (max offsets to use; default=10): ") or "10")
    except ValueError:
        context_depth = 10
    try:
        discount_factor = float(input("Enter discount factor (e.g., 2.0; default=100.0): ") or "100.0")
    except ValueError:
        discount_factor = 100.0
    initial_sentence = input("Enter an initial sentence (in Hebrew) [default='John Wick is a 2014 American action thriller film directed by Chad Stahelski and written by Derek Kolstad. The film stars Keanu']: ").strip() or 'John Wick is a 2014 American action thriller film directed by Chad Stahelski and written by Derek Kolstad. The film stars Keanu'
    try:
        num_to_generate = int(input("Enter number of words to generate [default=100]: ") or "100")
    except ValueError:
        num_to_generate = 100

    print("\nInitial sentence:")
    print(initial_sentence)
    print("\nGenerated words:")

    generated_tokens = generate_text(data, initial_sentence, num_to_generate, context_depth, discount_factor)
    full_sentence = " ".join(generated_tokens)
    print("\nFinal generated sentence:")
    print(full_sentence)

if __name__ == "__main__":
    main()
