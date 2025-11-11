# modules/validate_quotes.py
import os
import sys
import re
import json

def normalize_text(text):
    """
    Removes HTML tags and normalizes whitespace to prepare text for comparison.
    This ensures that minor formatting differences (like <u>) don't cause false negatives.
    """
    # Remove any HTML-like tags (e.g., <u>, <i>)
    text = re.sub(r'<[^>]+>', '', text)
    # Replace multiple whitespace characters (spaces, newlines, tabs) with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_original_quotes(keyword_dir):
    """
    Loads all original, full-text quotes from the initial search results.
    Returns a dictionary mapping {location_id: full_quote_text}.
    """
    originals = {}
    print("-> Loading original full-text quotes for comparison...")

    # Find the raw source files from the search step
    try:
        source_files = [f for f in os.listdir(keyword_dir) if f.endswith('.txt') and '_categorized' not in f and '_final' not in f]
        if not source_files:
            print(f"  ! Warning: No original source files found in {keyword_dir}.")
            return None

        for filename in source_files:
            filepath = os.path.join(keyword_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    originals[item['location']] = item['quote']

        print(f"  -> Loaded {len(originals)} original quotes.")
        return originals
    except Exception as e:
        print(f"  ! Error loading original quotes: {e}")
        return None

def run(final_file_path, original_quotes):
    """
    Validates a single final output file, adding [Warning] tags where excerpts
    are not verbatim substrings of their normalized originals.
    """
    keyword = os.path.basename(os.path.dirname(original_quotes['__source_dir__'])) # A bit of a hack to get the keyword

    print(f"\n----- Validating: {os.path.basename(final_file_path)} -----")

    try:
        with open(final_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"!!! ERROR: Could not read final output file: {e}")
        return

    warnings_added = 0
    quotes_processed = 0
    quote_template_regex = re.compile(r"(\{\{q\|)(.*?)(\|)(.*?)(\|)(.*?)(\}\})")

    for i, line in enumerate(lines):
        match = quote_template_regex.search(line)
        if match:
            quotes_processed += 1

            excerpt = match.group(2)
            location = match.group(4)

            if excerpt.startswith('[Warning]'):
                continue

            original_quote = original_quotes.get(location)
            if not original_quote:
                print(f"  ! Warning: No original text found for location '{location}'. Skipping.")
                continue

            normalized_original = normalize_text(original_quote)
            normalized_excerpt = normalize_text(excerpt.replace('...', ''))

            if normalized_excerpt not in normalized_original:
                warnings_added += 1
                new_line = line.replace(excerpt, f"[Warning] {excerpt}")
                lines[i] = new_line
                print(f"  -> Mismatch found for location {location}. Adding warning.")

    if warnings_added > 0:
        print(f"-> Found {warnings_added} potential issues out of {quotes_processed} quotes.")
        print(f"-> Overwriting file with warnings added.")
        with open(final_file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    else:
        print(f"-> Success! All {quotes_processed} quotes passed validation.")

if __name__ == '__main__':
    if len(sys.argv) not in [2, 3]:
        print("Usage: python modules/validate_quotes.py <keyword> [model_name]")
        print("  [model_name] is optional. If omitted, all existing final output files are validated.")
        sys.exit(1)

    keyword = sys.argv[1]

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keyword_dir = os.path.join(project_root, 'workspace', keyword)

    # Step 1: Load the original quotes once for efficiency
    original_quotes = load_original_quotes(keyword_dir)
    if not original_quotes:
        print("!!! Aborting validation: Could not load original quotes.")
        sys.exit(1)
    original_quotes['__source_dir__'] = keyword_dir # Store source for later

    # Step 2: Determine which files to validate
    files_to_validate = []
    if len(sys.argv) == 3:
        # A specific model was requested
        model_arg = sys.argv[2]
        model_name = ''
        if model_arg.lower() == 'chatgpt': model_name = 'ChatGPT'
        elif model_arg.lower() == 'gemini': model_name = 'Gemini'
        else:
            print(f"Error: Invalid model name '{model_arg}'.")
            sys.exit(1)
        files_to_validate.append(os.path.join(project_root, f'final_output_{model_name}_{keyword}.txt'))
    else:
        # Default: Find all possible output files
        print("No model specified. Searching for all final output files...")
        files_to_validate.append(os.path.join(project_root, f'final_output_{keyword}.txt'))
        files_to_validate.append(os.path.join(project_root, f'final_output_ChatGPT_{keyword}.txt'))
        files_to_validate.append(os.path.join(project_root, f'final_output_Gemini_{keyword}.txt'))

    # Step 3: Loop through the list and validate any that exist
    found_any_files = False
    for file_path in files_to_validate:
        if os.path.exists(file_path):
            found_any_files = True
            run(file_path, original_quotes)

    if not found_any_files:
        print(f"\n!!! ERROR: No final output files found for keyword '{keyword}'.")
        print("Ensure you have run the format_wiki.py script first.")
