# CreatePages-AI: AI-Powered Textual Analysis Tool

CreatePages-AI is a command-line tool designed to automate the process of searching, categorizing, and compiling quotes from the official Baha'i reference library. It uses a hybrid AI approach to leverage the unique strengths of different models, producing a thematically organized, wiki-formatted page of concise excerpts on any given topic.

## Workflow

The main script executes the following 5 scripts:

1.  **Search (`search_library.py`):** Searches bahai.org/library for a given keyword. It saves every paragraph where the keyword is found into structured JSON files in the `workspace/` directory, organized by source.

2.  **Categorize (`categorize_quotes.py`):** The script gathers all text from all the search results and sends them in a single request to the Gemini API. Gemini analyzes the text to identify overarching themes and assigns each quote to a category. 

3.  **Distill (`distill_quotes.py`):** The categorized, full-text quotes are then processed one-by-one using ChatGPT. Its task is to create a short, relevant excerpt from each paragraph.

4.  **Format (`format_wiki.py`):** This script takes the categorized and distilled quotes and assembles them into a final, clean text file formatted for MediaWiki. It organizes quotes under their category headings and uses a `{{q|...}}` template.

5.  **Validate (`validate_quotes.py`):** As a final QA step, this script compares every single distilled excerpt against its original source paragraph. If the excerpt is not a perfect, verbatim substring of the original, it prepends a `[Warning]` tag inside the quote template, flagging it for manual review.

The final result is a file in the root directory final_output_<model>_<keyword>.txt


## Setup Instructions

### 1. Prerequisites

-   Python 3.7+
-   API keys for both OpenAI (GPT-4) and Google AI (Gemini Pro).

### 2. Installation

Clone this repository

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Configuration

Move `.env.example` to `.env` and add your API keys

```bash
OPENAI_API_KEY="sk-..."
GEMINI_API_KEY="..."
BAHAI_LIBRARY_API_URL="https://xxxxxxxxxxxxxxx.us-east-1.aws.found.io/library/_search"
BAHAI_LIBRARY_AUTH_TOKEN="Basic xxxxxxxxxxxxxx"
```
To get the library API and URL

1.  Open your web browser (like Chrome or Firefox) and go to `https://www.bahai.org/library/`.
2.  Open the **Developer Tools** (usually by pressing `F12` or `Ctrl+Shift+I`).
3.  Go to the **Network** tab.
4.  In the library's search bar, type a simple word (like "God") and press Enter.
5.  In the Network tab, look for a new entry named `_search`. Click on it.
6.  In the "Headers" panel for that request, you will find:
    *   **Request URL:** This is the value for `BAHAI_LIBRARY_API_URL`.
    *   **Authorization:** This is the full value for `BAHAI_LIBRARY_AUTH_TOKEN` (it should start with `Basic ...`).

## Usage

### Main Workflow (Recommended)

To run the entire end-to-end process for a keyword, use the `main_process.py` script. This is the simplest and recommended way to use the tool.

```bash
python main_process.py <keyword>
```

**Example:**

```bash
python main_process.py government
```

This command will execute the full five-step pipeline. All intermediate files will be stored in `workspace/government/`, and the final, validated output will be saved in the root directory as `final_output_government.txt`.

### Individual Scripts (For Testing & Development)

You can also run each module individually. This is useful for refining prompts, re-running a specific step, or testing different AI models.

**Step 1: search_library.py**

```bash
python search_library.py <keyword>

Eg: python search_library.py government
```

**Step 2: categorize_quotes.py**

The token length is typically too long for the ChatGPT model, so we recommend Gemini

```bash
python search_library.py <keyword> [model_name]

Eg: python search_library.py government
Eg: python search_library.py government Gemini
```

**Step 3: distill_quotes.py**

```bash
python distill_quotes.py <keyword> [model_name] [file_name]

python distill_quotes.py government Gemini
python distill_quotes.py government ChatGPT government_kitab-i-iqan_categorized-Gemini.txt
```

**Step 4: format_wiki.py**

The previous step should have produced a file like book_title_final_for_wiki-ChatGPT.txt, therefore ChatGPT would be the [model_name] in this step.

```bash
python format_wiki.py <keyword> [model_name]

python format_wiki.py government Gemini
```

**Step 5: validate_quotes.py**

The previous step shold have produced a file like final_output_ChatGPT_government.txt depending on the model name you provided, use that in the next step:

```bash
python validate_quotes.py <keyword> [model_name]

python validate_quotes.py government Gemini
```
