# modules/categorize_quotes.py (UPDATED)
import os
import json
import string
try:
    from . import ai_processors
except ImportError:
    import ai_processors

BASE62_CHARS = string.digits + string.ascii_letters # 0-9, a-z, A-Z

def to_base_62(n, pad_to_length):
    """Converts an integer to a zero-padded base-62 string."""
    if n == 0:
        return BASE62_CHARS[0] * pad_to_length

    encoded = ""
    base = len(BASE62_CHARS)
    while n > 0:
        n, rem = divmod(n, base)
        encoded = BASE62_CHARS[rem] + encoded

    return encoded.zfill(pad_to_length) # Pad with leading zeros if needed

def parse_custom_format(raw_text, id_to_location_map, id_length):
    """Parses the model's custom text output back into a category map."""
    category_map = {}
    lines = raw_text.strip().split('\n')

    for line in lines:
        if ':' not in line:
            continue # Skip malformed lines

        category_name, ids_string = line.split(':', 1)
        category_name = category_name.strip()
        ids_string = ids_string.strip()

        locations = []
        for i in range(0, len(ids_string), id_length):
            seq_id = ids_string[i:i + id_length]
            original_location = id_to_location_map.get(seq_id)
            if original_location:
                locations.append(original_location)

        if locations:
            category_map[category_name] = locations

    return category_map

# The run function now accepts an optional log_file argument
def run(input_dir, output_dir, keyword, model_name, log_file=None):

    # --- NEW: Helper function for logging ---
    def log(message):
        """Prints to console and also writes to the log file if it exists."""
        print(message)
        if log_file:
            log_file.write(message + '\n')
            log_file.flush()

    log(f"\n----- Running Categorization (on full text) with {model_name} -----")

    if model_name.lower() == 'chatgpt':
        categorize_function = ai_processors.categorize_with_chatgpt
    elif model_name.lower() == 'gemini':
        categorize_function = ai_processors.categorize_with_gemini
    else:
        raise ValueError("Unsupported model. Choose 'chatgpt' or 'gemini'.")

    # 1. Aggregate all full quotes from original source files
    all_quotes_with_locations = []
    original_files_data = {}
    files_to_process = [f for f in os.listdir(input_dir) if f.startswith(keyword) and f.endswith('.txt') and '_distilled' not in f and '_organized' not in f and '_categorized' not in f and '_final' not in f]

    log("Aggregating all full paragraphs for categorization...")
    for filename in files_to_process:
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            original_files_data[filename] = data
            for item in data:
                all_quotes_with_locations.append({
                    "location": item['location'],
                    "quote": item['quote']
                })

    if not all_quotes_with_locations:
        log("No quotes found to categorize. Exiting.")
        return

    log("Mapping original locations to compact sequential IDs...")
    id_to_location_map = {}
    quotes_for_ai = []

    total_quotes = len(all_quotes_with_locations)
    # Calculate the fixed length needed for all IDs (e.g., for 1592 quotes, this will be 2)
    id_length = len(to_base_62(total_quotes - 1, 1))

    for i, item in enumerate(all_quotes_with_locations):
        sequential_id = to_base_62(i, id_length)
        original_location = item['location']

        id_to_location_map[sequential_id] = original_location
        quotes_for_ai.append({
            "id": sequential_id,
            "quote": item['quote']
        })
    log(f"Generated {total_quotes} sequential IDs of fixed length {id_length}.")

    # 2. Get the raw text mapping from the AI
    raw_text_response = categorize_function(quotes_for_ai, keyword, log_file=log_file)

    raw_output_path = os.path.join(output_dir, f'api_request_return_{model_name.lower()}.txt')
    log(f"Saving raw model output to {raw_output_path}...")
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(raw_text_response)

    # 3. Parse the custom format back into a standard dictionary
    log("Parsing custom text format back into a category map...")
    category_map = parse_custom_format(raw_text_response, id_to_location_map, id_length)

    # 4. Create a reverse map for easy lookup: {location -> category_name}
    location_to_category = {
        location: category
        for category, locations in category_map.items()
        for location in locations
    }

    # 4. Write new categorized files, preserving the full quote
    log("Writing categorized output files (with full quotes)...")
    for original_filename, items_list in original_files_data.items():
        base_name = os.path.splitext(original_filename)[0]
        output_filename = f"{base_name}_categorized-{model_name}.txt"
        output_path = os.path.join(output_dir, output_filename)

        categorized_data = []
        for item in items_list:
            category = location_to_category.get(item['location'], 'Uncategorized')
            new_item = item.copy()
            new_item['title'] = category
            categorized_data.append(new_item)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(categorized_data, f, indent=2, ensure_ascii=False)

        log(f"  -> Saved categorized output to {output_path}")

if __name__ == '__main__':
    import sys
    from dotenv import load_dotenv

    # Check for valid number of arguments (keyword, and optional model)
    if len(sys.argv) not in [2, 3]:
        print("Usage: python modules/categorize_quotes.py <keyword> [model_name]")
        print("  [model_name] is optional (ChatGPT or Gemini). If omitted, both are run.")
        print("\nExample (run both):")
        print("  python modules/categorize_quotes.py government")
        print("\nExample (run one):")
        print("  python modules/categorize_quotes.py government Gemini")
        sys.exit(1)

    load_dotenv()

    keyword = sys.argv[1]

    # Determine which models to process
    models_to_process = []
    if len(sys.argv) == 3:
        model_arg = sys.argv[2]
        if model_arg.lower() == 'chatgpt':
            models_to_process.append('ChatGPT')
        elif model_arg.lower() == 'gemini':
            models_to_process.append('Gemini')
        else:
            print(f"Error: Invalid model name '{model_arg}'. Please use 'ChatGPT' or 'Gemini'.")
            sys.exit(1)
    else:
        # Default case: no model specified, so run both
        models_to_process = ['ChatGPT', 'Gemini']

    # Set up paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    keyword_dir = os.path.join(project_root, 'workspace', keyword)

    print(f"--- Running categorization for keyword '{keyword}' for model(s): {', '.join(models_to_process)} ---")

    for model_name in models_to_process:
        run(keyword_dir, keyword_dir, keyword, model_name)

    print("\n--- All categorization complete. ---")
