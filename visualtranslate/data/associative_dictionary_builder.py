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

def load_existing_data(json_filename):
    """
    If the JSON file exists, load and return its contents.
    Otherwise, return None.
    """
    path = get_file_path(json_filename)
    if path and os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as infile:
            try:
                data = json.load(infile)
                return data
            except json.JSONDecodeError:
                print("Warning: Existing JSON is invalid. Starting fresh.")
                return None
    return None

def save_data(json_path, result):
    """Save the result dict as JSON to the specified path."""
    with open(json_path, 'w', encoding='utf-8') as outfile:
        json.dump(result, outfile, ensure_ascii=False, indent=2)

def process_text(input_file, context_size, word_data, word_to_id, id_to_word, next_id):
    """
    Process the input text file and update the live dictionary.
    For each token:
      - Increase its frequency ("seen").
      - Update its left ("L") and right ("R") associations using a weight 
        equal to 1/(distance) from the target.
      
    The context window is determined by context_size:
      - If context_size == -1, use all available tokens.
      - Otherwise, use up to context_size tokens on each side.
    
    Associations are stored as dictionaries mapping associated word ids (as strings) 
    to their cumulative weighted frequency.
    
    Returns updated word_data, word_to_id, id_to_word, and next available id.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    tokens = text.split()
    total_tokens = len(tokens)
    
    for i, token in enumerate(tokens):
        word = token.strip()
        if not word:
            continue

        # If word not seen, register it.
        if word not in word_to_id:
            word_to_id[word] = next_id
            id_to_word[str(next_id)] = word  # store keys as strings
            word_data[word] = {
                "id": next_id,
                "word": word,
                "seen": 0,
                "L": {},  # dictionary: associated word id (as string) -> weight
                "R": {}
            }
            next_id += 1

        # Update frequency count.
        word_data[word]["seen"] += 1

        # Determine context indices.
        if context_size == -1:
            left_indices = range(0, i)
            right_indices = range(i+1, total_tokens)
        else:
            left_indices = range(max(0, i - context_size), i)
            right_indices = range(i+1, min(total_tokens, i + 1 + context_size))

        # Process left context.
        for j in left_indices:
            assoc = tokens[j].strip()
            if not assoc:
                continue
            # Ensure the association word is registered.
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
            # Calculate weight based on distance (closer = higher weight).
            distance = i - j
            weight = 1.0 / distance if distance > 0 else 0
            # Update association in the left dictionary.
            word_data[word]["L"][assoc_id] = word_data[word]["L"].get(assoc_id, 0) + weight

        # Process right context.
        for k in right_indices:
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
            distance = k - i
            weight = 1.0 / distance if distance > 0 else 0
            word_data[word]["R"][assoc_id] = word_data[word]["R"].get(assoc_id, 0) + weight

    return word_data, word_to_id, id_to_word, next_id

def main():
    # File names.
    input_filename = "heb_text.txt"
    json_filename = "associative_data.json"
    
    input_path = get_file_path(input_filename)
    if input_path is None:
        sys.exit(f"Error: {input_filename} not found in the current directory or script directory.")
    print(f"Using input file: {input_path}")

    # Get context size from command-line arguments; default is 10.
    context_size = int(input("Enter context size (default 10): "))
    if len(sys.argv) > 1:
        try:
            context_size = int(sys.argv[1])
        except ValueError:
            print("Invalid context size provided; using default 10.")
    
    # Load existing data if available.
    existing_data = load_existing_data(json_filename)
    if existing_data:
        word_list = existing_data.get("words", [])
        mappings = existing_data.get("mappings", {})
        word_to_id = mappings.get("word_to_id", {})
        id_to_word = mappings.get("id_to_word", {})
        # Rebuild word_data from word_list. (If an entry lacks "word", try recovering from id_to_word.)
        word_data = {}
        for entry in word_list:
            if "word" not in entry:
                recovered = id_to_word.get(str(entry["id"]))
                if recovered:
                    entry["word"] = recovered
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

    # Process the input text to update the live dictionary.
    word_data, word_to_id, id_to_word, next_id = process_text(
        input_path, context_size, word_data, word_to_id, id_to_word, next_id
    )

    # Create a sorted list of word entries (sorted by their id).
    words_list = sorted(word_data.values(), key=lambda entry: entry["id"])
    
    # Prepare final JSON structure.
    result = {
        "words": words_list,
        "mappings": {
            "word_to_id": word_to_id,
            "id_to_word": id_to_word
        }
    }
    
    # Save the JSON file in the same directory as this script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, json_filename)
    save_data(output_path, result)
    
    print(f"Associative data saved to: {output_path}")

if __name__ == "__main__":
    main()
