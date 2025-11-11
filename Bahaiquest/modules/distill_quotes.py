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

    # Find the files that were just created by the categorize step
    source_suffix = source_model_name or model_name
    files_to_process = [f for f in os.listdir(input_dir) if f.endswith(f"_categorized-{source_suffix}.txt")]

    for filename in files_to_process:
        input_path = os.path.join(input_dir, filename)

        # Create the final output filename for the wiki formatter
        base_name = re.sub(r'_categorized-(ChatGPT|Gemini)\.txt$', '', filename)
        output_filename = f"{base_name}_final_for_wiki-{model_name}.txt"
        output_path = os.path.join(output_dir, output_filename)

        print(f"Processing {filename}...")

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        final_data = []
        for item in data:
            # Distill the full quote
            distilled_quote_text = distill_function(item['quote'], keyword)

            # Create the final object for the wiki formatter
            # The 'title' field now correctly holds the category
            final_item = {
                "title": item['title'], # This is the category from the previous step
                "location": item['location'],
                "quote": distilled_quote_text # This is the new distilled quote
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

    if len(sys.argv) not in [2, 3, 4]:
        # ... (help text is the same)
        sys.exit(1)

    load_dotenv()

    keyword = sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    keyword_dir = os.path.join(project_root, 'workspace', keyword)

    # The source of categorized files is ALWAYS Gemini in our workflow
    source_model = 'Gemini'

    if len(sys.argv) == 4:
        # Case 1: Single file mode
        model_name_arg = sys.argv[2]
        filename = sys.argv[3]
        if model_name_arg.lower() not in ['chatgpt', 'gemini']:
            print(f"Error: Invalid model name '{model_name_arg}'. Use 'ChatGPT' or 'Gemini'.")
            sys.exit(1)

        input_path = os.path.join(keyword_dir, filename)
        process_single_categorized_file(input_path, keyword_dir, keyword, model_name_arg.capitalize())
    else:
        # Case 2: Directory mode
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
        else:
            # No model specified, run both
            models_to_process = ['ChatGPT', 'Gemini']

        print(f"--- Running distillation for keyword '{keyword}' for model(s): {', '.join(models_to_process)} ---")
        print(f"--- (Reading source files categorized by {source_model}) ---")

        for model in models_to_process:
            # FIX: The key is passing source_model_name to the run function
            run(
                input_dir=keyword_dir,
                output_dir=keyword_dir,
                keyword=keyword,
                model_name=model,
                source_model_name=source_model
            )
        print("\n--- Distillation complete. ---")
