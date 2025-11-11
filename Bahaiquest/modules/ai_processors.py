# modules/ai_processors.py
import os
import json
import time
import openai
import google.generativeai as genai

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
You are an expert theological archivist specializing in the Baha'i Faith.
Your task is to analyze a list of full paragraphs, all containing the keyword "{keyword}", and group them by thematic category based on their context.

Rules:
1. Read all the paragraphs to identify 5-10 major, recurring themes.
2. Create a short, descriptive heading for each theme (e.g., "The role of just government", "Opposition from governments").
3. If a paragraph does not fit a common theme, assign it to a category named "Uncategorized".
4. The input is a JSON array of objects, where each object has a unique "location" and the full "quote" paragraph.
5. You MUST return the result as a single, valid JSON object. The keys of this object must be the category headings you created. The values must be an array of the original "location" strings that belong to that category.
6. Do not return the quote text. Return ONLY the location identifiers.

Example Output Format:
{{
  "Category Name A": ["location_id_1", "location_id_5"],
  "Category Name B": ["location_id_2", "location_id_3"],
  "Uncategorized": ["location_id_4"]
}}

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


def categorize_with_chatgpt(quotes_with_locations, keyword, max_retries=3):
    # This function is UPDATED
    print(f"  > Categorizing {len(quotes_with_locations)} full paragraphs with ChatGPT...")
    quotes_json = json.dumps(quotes_with_locations, indent=2)
    prompt = CATEGORIZATION_PROMPT.format(keyword=keyword, quotes_json=quotes_json)

    for attempt in range(max_retries):
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"    ! ChatGPT API error (Attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(5)
    # Return a fallback structure mapping all locations to Uncategorized
    all_locations = [q['location'] for q in quotes_with_locations]
    return {"Uncategorized": all_locations}


# --- Google (Gemini) Functions ---

def distill_with_gemini(paragraph, keyword, max_retries=3):
    # This function is unchanged
    print(f"  > Distilling with Gemini...")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = DISTILLATION_PROMPT.format(keyword=keyword, paragraph=paragraph)

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"    ! Gemini API error (Attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(5)
    return "[[Gemini distillation failed]]"


def categorize_with_gemini(quotes_with_locations, keyword, max_retries=3):
    # This function is UPDATED
    print(f"  > Categorizing {len(quotes_with_locations)} full paragraphs with Gemini...")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    quotes_json = json.dumps(quotes_with_locations, indent=2)
    prompt = CATEGORIZATION_PROMPT.format(keyword=keyword, quotes_json=quotes_json)

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
            return json.loads(response.text)
        except Exception as e:
            print(f"    ! Gemini API error (Attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(5)
    # Return a fallback structure mapping all locations to Uncategorized
    all_locations = [q['location'] for q in quotes_with_locations]
    return {"Uncategorized": all_locations}
