import json
import re
import os
from collections import defaultdict

# Define the mapping for file name components
abbreviation_map = {
    "days-remembrance": "DR",
    "epistle-son-wolf": "ESW",
    "gems-divine-mysteries": "GDM",
    "gleanings-writings-bahaullah": "GWB",
    "hidden-words": "HW",
    "kitab-i-aqdas": "KA",
    "kitab-i-iqan": "KI",
    "prayers-meditations-bahaullah": "PM",
    "call-divine-beloved": "CDB",
    "summons-lord-hosts": "SLH",
    "tabernacle-unity": "TU",
    "tablets-bahaullah": "TB",
    "additional-prayers-revealed-bahaullah": "APB",
    "additional-tablets-extracts-from-tablets-revealed-bahaullah": "ATB",
    "selections-writings-bab": "SWB",
    "memorials-faithful": "MF",
    "light-of-the-world": "LW",
    "paris-talks": "PT",
    "promulgation-universal-peace": "PUP",
    "secret-divine-civilization": "SDC",
    "selections-writings-abdul-baha": "SWAB",
    "some-answered-questions": "SAQ",
    "tablet-auguste-forel": "TAF",
    "tablets-divine-plan": "TDP",
    "tablets-hague-abdul-baha": "TTH",
    "travelers-narrative": "TN",
    "twelve-table-talks-abdul-baha": "TTT",
    "will-testament-abdul-baha": "WT",
    "prayers-abdul-baha": "TPR",
    "additional-tablets-extracts-talks-abdul-baha": "ATET",
    "additional-prayers-revealed-abdul-baha": "APR"
}

def run(input_dir, final_output_file, model_suffix):
    print(f"\n----- Formatting Wiki Output to {final_output_file} -----")

    all_quotes_by_category = defaultdict(list)
    keyword = os.path.basename(input_dir) # Get the keyword from the directory path

    text_files = [f for f in os.listdir(input_dir) if f.endswith(model_suffix)]

    if not text_files:
        print(f"No text files found in '{input_dir}' with suffix '{model_suffix}'.")
        return

    print(f"Found {len(text_files)} text files to format.")

    for filename in text_files:
        temp_key = filename.replace(f"{keyword}_", "")
        # Add re.IGNORECASE to make the match robust
        abbreviation_key = re.sub(r'_final_for_wiki-(ChatGPT|Gemini)\.txt$', '', temp_key, flags=re.IGNORECASE)

        abbreviation = abbreviation_map.get(abbreviation_key, "")
        if not abbreviation:
            print(f"  ! Warning: No abbreviation found for '{abbreviation_key}' in {filename}")

        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            category = item['title']
            location = item['location']
            quote = item['quote']

            # Use abbreviation if found, otherwise fall back to the location
            reference = abbreviation if abbreviation else location

            wiki_line = f"{{{{q|{quote}|{location}|{reference}}}}}"
            all_quotes_by_category[category].append(wiki_line)

    with open(final_output_file, 'w', encoding='utf-8') as f:
        # Sort categories alphabetically
        for category in sorted(all_quotes_by_category.keys()):
            f.write(f"== {category} ==\n")
            # Sort quotes within each category
            for quote_line in sorted(all_quotes_by_category[category]):
                f.write(f"{quote_line}\n")
            f.write("\n")

    print(f"-> Successfully wrote formatted output to {final_output_file}")

if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) not in [2, 3]:
        # ... (help text is the same)
        sys.exit(1)

    keyword = sys.argv[1]

    model_to_process = ''
    if len(sys.argv) == 3:
        model_arg = sys.argv[2]
        # FIX: Use .lower() for a case-insensitive check
        if model_arg.lower() == 'chatgpt':
            model_to_process = 'ChatGPT'
        elif model_arg.lower() == 'gemini':
            model_to_process = 'Gemini'
        else:
            print(f"Error: Invalid model name '{sys.argv[2]}'. Use 'ChatGPT' or 'Gemini'.")
            sys.exit(1)
    else:
        # Default to ChatGPT for the main pipeline output
        model_to_process = 'ChatGPT'

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_dir = os.path.join(project_root, 'workspace', keyword)

    # Determine output filename
    if len(sys.argv) == 2: # Default case
        final_output_file = os.path.join(project_root, f'final_output_{keyword}.txt')
    else: # Specific model test case
        final_output_file = os.path.join(project_root, f'final_output_{model_to_process}_{keyword}.txt')

    model_suffix = f'_final_for_wiki-{model_to_process}.txt'

    run(input_dir, final_output_file, model_suffix)
