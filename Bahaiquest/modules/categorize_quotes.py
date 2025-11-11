# modules/categorize_quotes.py (UPDATED)
import os
import json
try:
    from . import ai_processors
except ImportError:
    import ai_processors

def run(input_dir, output_dir, keyword, model_name):
    print(f"\n----- Running Categorization (on full text) with {model_name} -----")

    if model_name.lower() == 'chatgpt':
        categorize_function = ai_processors.categorize_with_chatgpt
    elif model_name.lower() == 'gemini':
        categorize_function = ai_processors.categorize_with_gemini
    else:
        raise ValueError("Unsupported model. Choose 'chatgpt' or 'gemini'.")

    # 1. Aggregate all full quotes from original source files
    all_quotes_with_locations = []
    # This map will store the full data from each original file
    original_files_data = {}

    # Find only the raw source files, ignore processed ones
    files_to_process = [f for f in os.listdir(input_dir) if f.startswith(keyword) and f.endswith('.txt') and '_distilled' not in f and '_organized' not in f and '_categorized' not in f and '_final' not in f]

    print("Aggregating all full paragraphs for categorization...")
    for filename in files_to_process:
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            original_files_data[filename] = data
            for item in data:
                # We only need location and the full quote for the AI
                all_quotes_with_locations.append({
                    "location": item['location'],
                    "quote": item['quote']
                })

    if not all_quotes_with_locations:
        print("No quotes found to categorize. Exiting.")
        return

    # 2. Get category-to-location mapping from the AI
    # e.g., {"Category A": ["loc1", "loc5"], "Category B": ["loc2"]}
    category_map = categorize_function(all_quotes_with_locations, keyword)

    # 3. Create a reverse map for easy lookup: {location -> category_name}
    location_to_category = {
        location: category
        for category, locations in category_map.items()
        for location in locations
    }

    # 4. Write new categorized files, preserving the full quote
    print("Writing categorized output files (with full quotes)...")
    for original_filename, items_list in original_files_data.items():
        base_name = os.path.splitext(original_filename)[0]
        output_filename = f"{base_name}_categorized-{model_name}.txt"
        output_path = os.path.join(output_dir, output_filename)

        categorized_data = []
        for item in items_list:
            category = location_to_category.get(item['location'], 'Uncategorized')
            new_item = item.copy()
            # Overwrite 'title' with the new category, keep original 'quote'
            new_item['title'] = category
            categorized_data.append(new_item)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(categorized_data, f, indent=2, ensure_ascii=False)

        print(f"  -> Saved categorized output to {output_path}")

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
