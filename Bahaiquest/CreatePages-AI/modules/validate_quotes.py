# modules/validate_quotes.py
import os
import sys
import re
import json

def load_original_quotes(keyword, keyword_dir):
    """
    Loads all original, full-text quotes from the initial search results.
    Returns a dictionary mapping {location_id: full_quote_text}.
    """
    originals = {}
    print("-> Loading original full-text quotes for comparison...")
    try:
        source_files = [f for f in os.listdir(keyword_dir) if f.startswith(keyword) and f.endswith('.txt') and '_categorized' not in f and '_final' not in f]
        if not source_files:
            print(f"  ! Warning: No original source files found in {keyword_dir}.")
            return None

        for filename in source_files:
            filepath = os.path.join(keyword_dir, filename)
            if os.path.getsize(filepath) == 0:
                print(f"  ! Warning: Skipping empty source file: {filename}")
                continue
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    originals[item['location']] = item['quote']

        print(f"  -> Loaded {len(originals)} original quotes.")
        return originals
    except json.JSONDecodeError as e:
        print(f"  ! FATAL Error: A source file is not valid JSON. Please check files in '{keyword_dir}'. Error: {e}")
        return None
    except Exception as e:
        print(f"  ! Error loading original quotes: {e}")
        return None

def _validate_and_update_wikitext_file(final_file_path, original_quotes_map):
    """
    Validates a single final WikiText output file. It parses {{q|...}} templates,
    checks for verbatim excerpts, and adds a '[Warning]' tag in-place for any mismatches.
    """
    print(f"\n----- Validating: {os.path.basename(final_file_path)} -----")

    try:
        with open(final_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"!!! ERROR: Could not read final output file: {e}")
        return

    warnings_added = 0
    quotes_processed = 0
    # Regex to capture the parts of the {{q|...}} template
    quote_template_regex = re.compile(r"(\{\{q\|)(.*?)(\|)(.*?)(\|)(.*?)(\}\})")

    for i, line in enumerate(lines):
        match = quote_template_regex.search(line)
        if match:
            quotes_processed += 1

            full_template = match.group(0)
            quote_prefix = match.group(1) # '{{q|'
            excerpt = match.group(2)
            pipe1 = match.group(3) # '|'
            location = match.group(4)
            pipe2 = match.group(5) # '|'
            source = match.group(6)
            template_suffix = '}}'

            # Skip lines that have already been marked with a warning
            if excerpt.strip().startswith('[Warning]'):
                continue

            original_quote = original_quotes_map.get(location)
            if not original_quote:
                print(f"  ! Warning: No original text found for location '{location}'. Skipping.")
                continue

            # Perform the strict, verbatim check as requested
            excerpt_for_check = excerpt.strip().strip('...').strip()

            if excerpt_for_check not in original_quote:
                warnings_added += 1
                # Reconstruct the line with the warning tag to preserve formatting
                new_excerpt = f"[Warning] {excerpt}"
                new_line = line.replace(excerpt, new_excerpt, 1) # Replace only the first occurrence
                lines[i] = new_line
                print(f"  -> Mismatch found for location {location}. Adding warning.")

    if warnings_added > 0:
        print(f"-> Found {warnings_added} issues out of {quotes_processed} quotes.")
        print(f"-> Overwriting file with warnings added.")
        with open(final_file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    else:
        print(f"-> Success! All {quotes_processed} quotes passed validation.")

def validate(keyword):
    """
    Main entry point for validation. Finds all final WikiText output files for a keyword,
    loads the original source quotes, and validates each file.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keyword_dir = os.path.join(project_root, 'workspace', keyword)

    original_quotes = load_original_quotes(keyword, keyword_dir)
    if not original_quotes:
        print("!!! Aborting validation: Could not load original quotes.")
        sys.exit(1)

    print("\nSearching for final WikiText output files to validate...")
    files_to_validate = []
    file_pattern_end = f'_{keyword}.txt'
    for filename in os.listdir(project_root):
        if filename.startswith('final_output_') and filename.endswith(file_pattern_end):
             files_to_validate.append(os.path.join(project_root, filename))

    if not files_to_validate:
        print(f"\n!!! ERROR: No final output files found for keyword '{keyword}' in root directory.")
        print("    Example expected filename: 'final_output_ChatGPT_power.txt'")
        return

    for file_path in files_to_validate:
        if os.path.exists(file_path):
            _validate_and_update_wikitext_file(file_path, original_quotes)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python modules/validate_quotes.py <keyword>")
        print("  This will automatically find and validate all 'final_output_*_<keyword>.txt' files.")
        sys.exit(1)

    validate(keyword=sys.argv[1])
