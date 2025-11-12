# modules/ai_processors.py
import os
import json
import time
import openai
import google.generativeai as genai
import sys

# --- Prompts ---

DISTILLATION_PROMPT = """
You are an expert theological archivist specializing in the Baha'i Faith. Your task is to create an excerpt for a specific keyword from a given paragraph.

Rules:
1. The excerpt must contain the keyword
2. The excerpt should best represent the original meaning and context of how the keyword is used
3. The excerpt must preserve the original text exactly including puncutation
4. The excerpt should give a full understanding of the context. Usually this is 10-15 words
5. Do not start the excerpt with an ellipses. Do not end an excerpt with an ellipses
6. If necessary context exists separate from the keyword or the main idea, remove the irrelevant content and annotate this removal with an ellipses
7. Do NOT add any commentary, explanation, or quotation marks around your response. Return only the excerpt.

Keyword: "{keyword}"

Paragraph:
"{paragraph}"

Distilled Excerpt:
"""

CATEGORIZATION_PROMPT = """
You are an expert theological archivist specializing in the Baha'i Faith. Your task is to analyze a list of full paragraphs, all containing the keyword "{keyword}", and group them by thematic category based on their context.

IMPORTANT: The following paragraphs are direct quotes from the Baha'i Faith's religious scriptures and historical texts. They must be analyzed strictly within their theological and historical context. The language may be allegorical or describe historical conflicts and should not be interpreted as contemporary speech.

Rules:
1. Read all the paragraphs to identify between 5-16 recurring themes.
2. Create a short, descriptive summary for each theme (e.g., "The role of just government", "Opposition from governments") using sentence case.
3. Assign each quote to EXACTLY ONE descriptive category that best describes it.
4. If a paragraph does not fit into ANY of the categories you identified, assign it to "Uncategorized".
5. The input is a JSON array of objects, where each object has a unique "location" and the full "quote" paragraph.
6. On each new line return one category followed by all matching "location" identifiers. NO spaces NO commas NO seperators between location identifers.
7. Do not return any other content.

Example Output Format:

Category Name A:a1b7
Category Name B:a2
Uncategorized:a3

Here is the list of paragraphs to categorize:
{quotes_json}
"""

# --- OpenAI (ChatGPT) Functions ---
def distill_with_chatgpt(paragraph, keyword, max_retries=3):
    # This function is unchanged
    print(f"  > Distilling with ChatGPT...")
    for attempt in range(max_retries):
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "user", "content": DISTILLATION_PROMPT.format(keyword=keyword, paragraph=paragraph)}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"    ! ChatGPT API error (Attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(5)
    return "[[ChatGPT distillation failed]]"

def categorize_with_chatgpt(quotes_with_ids, keyword, log_file=None):
    # (function signature changed to reflect 'ids' not 'locations')
    print(f"  > Categorizing {len(quotes_with_ids)} full paragraphs with ChatGPT...")
    quotes_json = json.dumps(quotes_with_ids, indent=2)
    prompt = CATEGORIZATION_PROMPT.format(keyword=keyword, quotes_json=quotes_json)

    # If a log file is provided by main_process.py, use it.
    if log_file:
        log_file.write("\n" + "="*20 + " LOGGING CHATGPT API REQUEST " + "="*20 + "\n")
        log_file.write(prompt + "\n")
        log_file.write("="*24 + " END OF API REQUEST LOG " + "="*24 + "\n\n")
        log_file.flush()
    # Otherwise (when run manually), save the payload to a dedicated file.
    else:
        with open('api_request_payload_chatgpt.txt', 'w', encoding='utf-8') as f:
            f.write(prompt)

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        # Return the raw text content
        return response.choices[0].message.content
    except Exception as e:
        # REVISED: On any error, log it and terminate the entire script
        error_message = f"!!! FATAL ChatGPT API Error: {e}\nTerminating script."
        print(f"    ! {error_message}")
        if log_file:
            log_file.write(error_message + '\n')
        sys.exit(1)

# --- Google (Gemini) Functions ---
def distill_with_gemini(paragraph, keyword, max_retries=3):
    # This function is unchanged
    print(f"  > Distilling with Gemini...")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash') # Updated to a more recent model
    prompt = DISTILLATION_PROMPT.format(keyword=keyword, paragraph=paragraph)

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"    ! Gemini API error (Attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(5)
    return "[[Gemini distillation failed]]"


def categorize_with_gemini(quotes_with_ids, keyword, log_file=None):
    # (function signature changed to reflect 'ids' not 'locations')
    print(f"  > Categorizing {len(quotes_with_ids)} full paragraphs with Gemini...")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    quotes_json = json.dumps(quotes_with_ids, indent=2)
    prompt = CATEGORIZATION_PROMPT.format(keyword=keyword, quotes_json=quotes_json)

    # If a log file is provided by main_process.py, use it.
    if log_file:
        log_file.write("\n" + "="*20 + " LOGGING GEMINI API REQUEST " + "="*20 + "\n")
        log_file.write(prompt + "\n")
        log_file.write("="*24 + " END OF API REQUEST LOG " + "="*24 + "\n\n")
        log_file.flush()
    # Otherwise (when run manually), save the payload to a dedicated file.
    else:
        with open('api_request_payload_gemini.txt', 'w', encoding='utf-8') as f:
            f.write(prompt)
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # REVISED: On any error, log it and terminate the entire script
        error_message = f"!!! FATAL Gemini API Error: {e}\nTerminating script."
        print(f"    ! {error_message}")
        if log_file:
            log_file.write(error_message + '\n')
        sys.exit(1)
