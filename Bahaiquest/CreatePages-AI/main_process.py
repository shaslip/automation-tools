r"""
Usage: python main_process.py <keyword>
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Import our custom modules
from modules import categorize_quotes, distill_quotes, format_wiki, validate_quotes

# --- NEW: Helper function to print to console AND log file ---
def log_and_print(message, log_file):
    """Prints a message to the console and appends it to the log file."""
    print(message)
    log_file.write(message + '\n')
    log_file.flush() # Ensure the message is written immediately

def main(keyword):
    # --- Setup Logging ---
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f'{keyword}.log')

    # Open the log file for the entire duration of the workflow
    with open(log_file_path, 'w', encoding='utf-8') as log_file:
        log_and_print(f"========= STARTING HYBRID WORKFLOW FOR KEYWORD: '{keyword}' =========", log_file)
        log_and_print("Using Gemini for Categorization and ChatGPT for Distillation.", log_file)
        log_and_print(f"Detailed output will be saved to: {log_file_path}", log_file)
        load_dotenv()

        KEYWORD_DIR = os.path.join('workspace', keyword)
        os.makedirs(KEYWORD_DIR, exist_ok=True)

        # --- Step 1: Search the Library ---
        search_script_path = 'modules/search_library.py'
        log_and_print(f"\n----- Step 1: Running Search -----", log_file)
        try:
            # Redirect stdout and stderr of the subprocess directly to the log file
            # This will capture all the 'print' statements from search_library.py
            subprocess.run(
                ['python', search_script_path, keyword, KEYWORD_DIR],
                check=True,
                stdout=log_file,            # Send standard output to the log file
                stderr=subprocess.STDOUT    # Merge standard error into standard output
            )
            log_and_print("----- Search Complete -----", log_file)
        except FileNotFoundError:
            log_and_print(f"!!! ERROR: Search script not found at '{search_script_path}'.", log_file)
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            # The error details are already in the log file because we redirected stderr
            log_and_print(f"!!! ERROR: Your search script failed with a non-zero exit code: {e.returncode}", log_file)
            log_and_print(f"!!! Check '{log_file_path}' for detailed error messages.", log_file)
            sys.exit(1)

        # --- Subsequent Steps ---
        # NOTE: The output from these imported modules will still print to the console
        # unless they are also modified to accept a log_file object.
        # For now, only their status messages from this script are logged.

        log_and_print("\n----- Step 2: Categorizing with Gemini -----", log_file)
        categorize_quotes.run(KEYWORD_DIR, KEYWORD_DIR, keyword, model_name='Gemini', log_file=log_file)

        log_and_print("\n----- Step 3: Distilling with ChatGPT -----", log_file)
        distill_quotes.run(
            input_dir=KEYWORD_DIR,
            output_dir=KEYWORD_DIR,
            keyword=keyword,
            model_name='ChatGPT',
            source_model_name='Gemini'
        )

        log_and_print("\n----- Step 4: Formatting Final Wiki Output -----", log_file)
        format_wiki.run(
            input_dir=KEYWORD_DIR,
            final_output_file=f'final_output_{keyword}.txt',
            model_suffix='_final_for_wiki-ChatGPT.txt'
        )

        log_and_print("\n----- Step 5: Validating Excerpts Against Originals -----", log_file)
        validate_quotes.run(keyword)

        log_and_print(f"\n========= WORKFLOW COMPLETE FOR '{keyword}' =========", log_file)
        print(f"All intermediate files are in: {KEYWORD_DIR}")
        print(f"Final validated output is in: final_output_{keyword}.txt")
        print(f"Full execution log is available at: {log_file_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main_process.py <keyword>")
        sys.exit(1)

    search_keyword = sys.argv[1].lower()
    main(search_keyword)

