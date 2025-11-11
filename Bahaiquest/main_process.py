import os
import sys
import subprocess
from dotenv import load_dotenv

# Import our custom modules
from modules import categorize_quotes, distill_quotes, format_wiki, validate_quotes

def main(keyword):
    print(f"========= STARTING HYBRID WORKFLOW FOR KEYWORD: '{keyword}' =========")
    print("Using Gemini for Categorization and ChatGPT for Distillation.")
    load_dotenv()

    KEYWORD_DIR = os.path.join('workspace', keyword)
    os.makedirs(KEYWORD_DIR, exist_ok=True)

    # --- Step 1: Search the Library ---
    search_script_path = 'modules/search_library.py'
    print(f"\n----- Step 1: Running Search -----")
    # ... (subprocess call is the same) ...
    try:
        subprocess.run(
            ['python', search_script_path, keyword, KEYWORD_DIR],
            check=True, capture_output=True, text=True
        )
        print("----- Search Complete -----")
    except FileNotFoundError:
        print(f"!!! ERROR: Search script not found at '{search_script_path}'.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"!!! ERROR: Your search script failed with the following error:")
        print(e.stderr)
        sys.exit(1)

    # --- Step 2: Categorize Quotes (using Gemini) ---
    print("\n----- Step 2: Categorizing with Gemini -----")
    categorize_quotes.run(KEYWORD_DIR, KEYWORD_DIR, keyword, model_name='Gemini')

    # --- Step 3: Distill Quotes (using ChatGPT on Gemini's output) ---
    print("\n----- Step 3: Distilling with ChatGPT -----")
    distill_quotes.run(
        input_dir=KEYWORD_DIR,
        output_dir=KEYWORD_DIR,
        keyword=keyword,
        model_name='ChatGPT',
        source_model_name='Gemini'
    )

    # --- Step 4: Format Final Wiki Output ---
    print("\n----- Step 4: Formatting Final Wiki Output -----")
    format_wiki.run(
        input_dir=KEYWORD_DIR,
        final_output_file=f'final_output_{keyword}.txt',
        model_suffix='_final_for_wiki-ChatGPT.txt'
    )

    # --- Step 5: Final Validation (NEW) ---
    print("\n----- Step 5: Validating Excerpts Against Originals -----")
    validate_quotes.run(keyword)


    print(f"\n========= WORKFLOW COMPLETE FOR '{keyword}' =========")
    print(f"All intermediate files are in: {KEYWORD_DIR}")
    print(f"Final validated output is in: final_output_{keyword}.txt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main_process.py <keyword>")
        sys.exit(1)

    search_keyword = sys.argv[1].lower()
    main(search_keyword)
