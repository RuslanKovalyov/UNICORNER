#!/usr/bin/env python3
import os
import sys
import json

def get_file_path(filename):
    """
    Check if the file exists in the current working directory.
    If not, check in the directory where this script is located.
    Returns the absolute path if found; otherwise, returns None.
    """
    if os.path.exists(filename):
        return os.path.abspath(filename)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, filename)
    if os.path.exists(candidate):
        return candidate
    return None

def process_text(input_file, context_size=10):
    """
    Processes the text file to build a live dictionary of words.
    
    For each word, it stores:
      - "id": a unique identifier (rank) assigned when the word is first seen.
      - "seen": a frequency count (how many times the word appears).
      - "L": a list of left context words (from each occurrence).
      - "R": a list of right context words (from each occurrence).
    
    The context is collected from each occurrence using the provided context_size:
      - If context_size == -1, it takes all words on the left/right.
      - Otherwise, it takes at most context_size words on each side.
    
    Returns:
      word_data: dict with word keys and their info.
      word_to_id: mapping from word to its id.
      id_to_word: mapping from id (as int) to word.
    """
    word_data = {}    # key: word, value: dict with "id", "seen", "L", and "R"
    word_to_id = {}
    id_to_word = {}
    next_id = 1

    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Simple tokenization by whitespace (we do not split into sentences)
    tokens = text.split()
    
    for i, token in enumerate(tokens):
        word = token.strip()
        if not word:
            continue

        # Register the word if not seen before
        if word not in word_to_id:
            word_to_id[word] = next_id
            id_to_word[next_id] = word
            word_data[word] = {
                "id": next_id,
                "seen": 0,
                "L": [],
                "R": []
            }
            next_id += 1

        # Update the frequency count
        word_data[word]["seen"] += 1

        # Get left and right context from the token list
        if context_size == -1:
            left_context = tokens[:i]
            right_context = tokens[i+1:]
        else:
            left_context = tokens[max(0, i - context_size): i]
            right_context = tokens[i+1: i+1+context_size]

        word_data[word]["L"].extend(left_context)
        word_data[word]["R"].extend(right_context)
    
    return word_data, word_to_id, id_to_word

def main():
    # Input file name (change to your source file, e.g. a full book or a raw list)
    input_filename = "heb_text.txt"
    # Output JSON file
    output_filename = "associative_data.json"
    
    input_path = get_file_path(input_filename)
    if input_path is None:
        sys.exit(f"Error: {input_filename} not found in the current directory or script directory.")
    
    print(f"Using input file: {input_path}")
    
    # Read the context size from a command-line argument if provided;
    # default is 10 (set to -1 to capture all available left/right words).
    context_size = 10
    if len(sys.argv) > 1:
        try:
            context_size = int(sys.argv[1])
        except ValueError:
            print("Invalid context size provided, using default 10.")
    
    word_data, word_to_id, id_to_word = process_text(input_path, context_size=context_size)
    
    # Create a sorted list of word objects based on their assigned id (rank)
    words_list = []
    for word, info in sorted(word_data.items(), key=lambda item: item[1]["id"]):
        words_list.append({
            "rank": info["id"],
            "word": word,
            "seen": info["seen"],
            "L": info["L"],
            "R": info["R"]
        })
    
    # Prepare the final JSON structure including mappings
    result = {
        "words": words_list,
        "mappings": {
            "word_to_id": word_to_id,
            "id_to_word": id_to_word
        }
    }
    
    # Write output JSON file to the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(result, outfile, ensure_ascii=False, indent=2)
    
    print(f"Associative data saved to: {output_path}")

if __name__ == "__main__":
    main()
