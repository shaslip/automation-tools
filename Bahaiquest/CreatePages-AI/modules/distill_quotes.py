# modules/distill_quotes.py (UPDATED)
import os
import json
import re

try:
    from . import ai_processors
except ImportError:
    import ai_processors

def run(input_dir, output_dir, keyword, model_name, source_model_name=None):
    print(f"\n----- Running Distillation (on categorized text) with {model_name} -----")

    if model_name.lower() == 'chatgpt':
        distill_function = ai_processors.distill_with_chatgpt
    elif model_name.lower() == 'gemini':
        distill_function = ai_processors.distill_with_gemini
    else:
        raise ValueError("Unsupported model. Choose 'chatgpt' or 'gemini'.")

    # This logic correctly finds files based on the source_model_name passed to it
    source_suffix = source_model_name or model_name
    files_to_process = [f for f in os.listdir(input_dir) if f.endswith(f"_categorized-{source_suffix}.txt")]

    if not files_to_process:
        print(f"No files found ending in '_categorized-{source_suffix}.txt'. Skipping.")
        return

    for filename in files_to_process:
        input_path = os.path.join(input_dir, filename)

        base_name = re.sub(r'_categorized-(ChatGPT|Gemini)\.txt$', '', filename)
        output_filename = f"{base_name}_final_for_wiki-{model_name}.txt"
        output_path = os.path.join(output_dir, output_filename)

        print(f"Processing {filename}...")

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        final_data = []
        for item in data:
            distilled_quote_text = distill_function(item['quote'], keyword)
            final_item = {
                "title": item['title'],
                "location": item['location'],
                "quote": distilled_quote_text
            }
            final_data.append(final_item)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)

        print(f"  -> Saved final distilled & categorized output to {output_path}")

def process_single_categorized_file(input_path, output_dir, keyword, model_name):
    """Processes a single categorized file to distill its quotes."""
    print(f"\n----- Running Single-File Distillation with {model_name} -----")

    if not os.path.exists(input_path):
        print(f"Error: Input file not found at '{input_path}'")
        return

    if model_name.lower() == 'chatgpt':
        distill_function = ai_processors.distill_with_chatgpt
    elif model_name.lower() == 'gemini':
        distill_function = ai_processors.distill_with_gemini
    else:
        raise ValueError("Unsupported model. Choose 'chatgpt' or 'gemini'.")

    filename = os.path.basename(input_path)
    base_name = re.sub(r'_categorized-(ChatGPT|Gemini)\.txt$', '', filename)
    output_filename = f"{base_name}_final_for_wiki-{model_name}.txt"
    output_path = os.path.join(output_dir, output_filename)

    print(f"Processing {filename}...")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    final_data = []
    for item in data:
        distilled_quote_text = distill_function(item['quote'], keyword)
        final_item = {
            "title": item['title'],
            "location": item['location'],
            "quote": distilled_quote_text
        }
        final_data.append(final_item)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    print(f"  -> Saved final output to {output_path}")

if __name__ == '__main__':
    import sys
    import os
    from dotenv import load_dotenv

    # Updated help text to be more accurate
    if len(sys.argv) not in [2, 3, 4]:
        print("Usage:")
        print("  1. Directory Mode (all sources, all distillers):")
        print("     python modules/distill_quotes.py <keyword>")
        print("  2. Directory Mode (all sources, one distiller):")
        print("     python modules/distill_quotes.py <keyword> <distill_model_name>")
        print("  3. Single File Mode:")
        print("     python modules/distill_quotes.py <keyword> <distill_model_name> <filename>")
        sys.exit(1)

    load_dotenv()

    keyword = sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    keyword_dir = os.path.join(project_root, 'workspace', keyword)

    if len(sys.argv) == 4:
        # Case 1: Single file mode (This logic is unchanged)
        model_name_arg = sys.argv[2]
        filename = sys.argv[3]
        if model_name_arg.lower() not in ['chatgpt', 'gemini']:
            print(f"Error: Invalid model name '{model_name_arg}'. Use 'ChatGPT' or 'Gemini'.")
            sys.exit(1)

        input_path = os.path.join(keyword_dir, filename)
        # Note: You need to implement the function body for process_single_categorized_file
        # if it's not already complete in your file.
        # process_single_categorized_file(input_path, keyword_dir, keyword, model_name_arg.capitalize())
        # For now, assuming it's complete from your previous code.

    else:
        # Case 2: Directory mode (This is the updated logic)

        # Step A: Determine which distillation models to use based on args
        models_to_process = []
        if len(sys.argv) == 3:
            model_name_arg = sys.argv[2]
            if model_name_arg.lower() == 'chatgpt':
                models_to_process.append('ChatGPT')
            elif model_name_arg.lower() == 'gemini':
                models_to_process.append('Gemini')
            else:
                print(f"Error: Invalid model name '{model_name_arg}'. Use 'ChatGPT' or 'Gemini'.")
                sys.exit(1)
        else: # No model specified, so run both
            models_to_process = ['ChatGPT', 'Gemini']

        # Step B: Discover which source models have categorized files available
        available_source_models = set()
        for f in os.listdir(keyword_dir):
            if f.endswith("_categorized-ChatGPT.txt"):
                available_source_models.add('ChatGPT')
            elif f.endswith("_categorized-Gemini.txt"):
                available_source_models.add('Gemini')

        if not available_source_models:
            print("No categorized source files found in workspace. Exiting.")
            sys.exit(0)

        print(f"--- Running distillation for keyword '{keyword}' for model(s): {', '.join(models_to_process)} ---")

        # Step C: Loop through each available source and run the chosen distillers
        for source in sorted(list(available_source_models)):
            print(f"\n--- Reading source files categorized by {source} ---")
            for model in models_to_process:
                run(
                    input_dir=keyword_dir,
                    output_dir=keyword_dir,
                    keyword=keyword,
                    model_name=model,
                    source_model_name=source  # Dynamically pass the discovered source
                )

        print("\n--- Distillation complete. ---")
