#!/usr/bin/env python3
import os
import sys
import json
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

def load_existing_data(json_filename):
    """Load existing JSON data if it exists; otherwise, return None."""
    path = get_file_path(json_filename)
    if path and os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as infile:
                data = json.load(infile)
                # Check for required keys.
                if "words" in data and "mappings" in data:
                    return data
        except json.JSONDecodeError:
            print("Warning: Existing JSON is invalid. Starting fresh.")
    return None

def save_data(json_path, result):
    """Save the result dictionary as JSON to the specified path."""
    with open(json_path, 'w', encoding='utf-8') as outfile:
        json.dump(result, outfile, ensure_ascii=False, indent=2)
    print(f"Associative data saved to: {json_path}")

def process_text(input_file, context_depth, word_data, word_to_id, id_to_word, next_id):
    """
    Process the input text file and update the live dictionary.
    For each token in the text, update its "seen" count and record left/right associations.
    Associations are stored by offset position:
      "L": { "1": {assoc_id: weight, ...}, "2": {...}, ... }
      "R": { "1": {assoc_id: weight, ...}, "2": {...}, ... }
    Weight is computed as 1.0/distance.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    tokens = text.split()
    total_tokens = len(tokens)
    
    for i, token in enumerate(tokens):
        word = token.strip()
        if not word:
            continue
        # Register new word if needed.
        if word not in word_to_id:
            word_to_id[word] = next_id
            id_to_word[str(next_id)] = word
            word_data[word] = {
                "id": next_id,
                "word": word,
                "seen": 0,
                "L": {},  # left associations by offset (keys as string "1", "2", …)
                "R": {}   # right associations by offset
            }
            next_id += 1
        word_data[word]["seen"] += 1

        # Process left context: for each offset from 1 to context_depth (if available)
        for offset in range(1, context_depth + 1):
            j = i - offset
            if j < 0:
                break
            assoc = tokens[j].strip()
            if not assoc:
                continue
            if assoc not in word_to_id:
                word_to_id[assoc] = next_id
                id_to_word[str(next_id)] = assoc
                word_data[assoc] = {
                    "id": next_id,
                    "word": assoc,
                    "seen": 0,
                    "L": {},
                    "R": {}
                }
                next_id += 1
            assoc_id = str(word_to_id[assoc])
            # Weight: 1.0/offset
            weight = 1.0 / offset
            # Update target word's left association for this offset.
            offset_key = str(offset)
            word_data[word]["L"].setdefault(offset_key, {})
            word_data[word]["L"][offset_key][assoc_id] = word_data[word]["L"][offset_key].get(assoc_id, 0) + weight

        # Process right context similarly.
        for offset in range(1, context_depth + 1):
            k = i + offset
            if k >= total_tokens:
                break
            assoc = tokens[k].strip()
            if not assoc:
                continue
            if assoc not in word_to_id:
                word_to_id[assoc] = next_id
                id_to_word[str(next_id)] = assoc
                word_data[assoc] = {
                    "id": next_id,
                    "word": assoc,
                    "seen": 0,
                    "L": {},
                    "R": {}
                }
                next_id += 1
            assoc_id = str(word_to_id[assoc])
            weight = 1.0 / offset
            offset_key = str(offset)
            word_data[word]["R"].setdefault(offset_key, {})
            word_data[word]["R"][offset_key][assoc_id] = word_data[word]["R"][offset_key].get(assoc_id, 0) + weight

    # Build a sorted list of word entries (by id).
    words_list = sorted(word_data.values(), key=lambda entry: entry["id"])
    return {
        "words": words_list,
        "mappings": {
            "word_to_id": word_to_id,
            "id_to_word": id_to_word
        }
    }, next_id

def main():
    # File names.
    input_filename = "heb_text.txt"
    json_filename = "offset_position_associative_data.json"

    input_path = get_file_path(input_filename)
    if input_path is None:
        sys.exit(f"Error: {input_filename} not found.")
    print(f"Using input file: {input_path}")

    # Ask user for context depth.
    try:
        context_depth = int(input("Enter context depth (number of tokens to record for associations; -1 for full context) [default=10]: ") or "10")
        if context_depth == -1:
            print("Full context is not supported in the new format; using default 10.")
            context_depth = 10
    except ValueError:
        context_depth = 10

    # Load existing data if available.
    existing_data = load_existing_data(json_filename)
    if existing_data:
        word_list = existing_data.get("words", [])
        mappings = existing_data.get("mappings", {})
        word_to_id = mappings.get("word_to_id", {})
        id_to_word = mappings.get("id_to_word", {})
        # Rebuild word_data dictionary from word_list.
        word_data = {}
        for entry in word_list:
            if "word" not in entry and str(entry["id"]) in id_to_word:
                entry["word"] = id_to_word[str(entry["id"])]
            word_data[entry["word"]] = entry
        if id_to_word:
            next_id = max(int(k) for k in id_to_word.keys()) + 1
        else:
            next_id = 1
    else:
        word_data = {}
        word_to_id = {}
        id_to_word = {}
        next_id = 1

    # Process text to update dictionary.
    result, next_id = process_text(input_path, context_depth, word_data, word_to_id, id_to_word, next_id)
    # Save result
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, json_filename)
    save_data(output_path, result)

if __name__ == "__main__":
    main()
