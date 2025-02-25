#!/usr/bin/env python3
import os
import sys

def get_file_path(filename):
    """
    Check if the file exists in the current working directory.
    If not, check in the directory of the script.
    Returns the absolute path if found; otherwise, returns None.
    """
    # Check current working directory
    if os.path.exists(filename):
        return os.path.abspath(filename)
    
    # Check in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, filename)
    if os.path.exists(candidate):
        return candidate
    
    return None

def is_hebrew(word):
    """Return True if the word contains any Hebrew characters (Unicode range U+0590 to U+05FF)."""
    return any('\u0590' <= ch <= '\u05FF' for ch in word)

def extract_last_hebrew_word(line):
    """
    Splits a line into tokens and returns the last token that contains Hebrew characters.
    If no token contains Hebrew characters, returns None.
    """
    tokens = line.strip().split()
    for token in reversed(tokens):
        if is_hebrew(token):
            return token.strip()
    return None

def main():
    input_filename = "frequency_list.txt"
    output_filename = "cleaned_frequency_list.txt"
    
    input_path = get_file_path(input_filename)
    if input_path is None:
        sys.exit(f"Error: {input_filename} not found in the current directory or the script directory.")
    
    print(f"Using input file: {input_path}")
    
    # Write output file to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_filename)
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        for line in infile:
            if line.strip():
                word = extract_last_hebrew_word(line)
                if word:
                    outfile.write(word + "\n")
    
    print(f"Cleaned list saved to: {output_path}")

if __name__ == "__main__":
    main()
