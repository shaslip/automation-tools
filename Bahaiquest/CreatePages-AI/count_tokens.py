import os
import sys
from dotenv import load_dotenv

def count_gemini_tokens(text_content):
    """Counts tokens using the Google Gemini API."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # IMPORTANT: Using the specific model you provided.
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.count_tokens(text_content)
        return response.total_tokens
    except ImportError:
        print("ERROR: 'google-generativeai' library not found. Please run 'pip install google-generativeai'")
        return None
    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        return None

def count_chatgpt_tokens(text_content):
    """Counts tokens locally using OpenAI's tiktoken library."""
    try:
        import tiktoken
        # This encoding is for the gpt-4-turbo model used in your script.
        encoding = tiktoken.encoding_for_model("gpt-4-turbo")
        token_list = encoding.encode(text_content)
        return len(token_list)
    except ImportError:
        print("ERROR: 'tiktoken' library not found. Please run 'pip install tiktoken'")
        return None
    except Exception as e:
        print(f"An error occurred with tiktoken: {e}")
        return None

def main():
    """Main function to run the token counter from the command line."""
    if len(sys.argv) != 3:
        print("Usage: python count_tokens.py <file_path> <model_name>")
        print("  <model_name> must be 'gemini' or 'chatgpt'")
        sys.exit(1)

    file_path = sys.argv[1]
    model_name = sys.argv[2].lower()

    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        sys.exit(1)

    load_dotenv()

    print(f"Reading file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    token_count = None
    if model_name == 'gemini':
        print("Counting tokens for Gemini...")
        token_count = count_gemini_tokens(content)
    elif model_name == 'chatgpt':
        print("Counting tokens for ChatGPT...")
        token_count = count_chatgpt_tokens(content)
    else:
        print(f"Error: Unknown model '{model_name}'. Please use 'gemini' or 'chatgpt'.")
        sys.exit(1)

    if token_count is not None:
        print("-" * 30)
        print(f"Total tokens for {model_name}: {token_count}")
        print("-" * 30)

if __name__ == "__main__":
    main()
