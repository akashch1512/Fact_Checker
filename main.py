import google.generativeai as genai
import os
import sys
import textwrap
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# API key should NEVER be hardcoded.  Use environment variables!
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logging.critical("GEMINI_API_KEY environment variable not set.  Exiting.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Model selection with fallback and logging
try:
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    logging.info("Initialized Gemini 1.5 Flash model.")
except Exception as e:
    logging.warning(f"Could not initialize 'gemini-1.5-flash' model. Attempting 'gemini-pro'. Error: {e}")
    try:
        model = genai.GenerativeModel(model_name="gemini-pro")
        logging.info("Initialized Gemini Pro model as fallback.")
    except Exception as e_fallback:
        logging.critical(f"Could not initialize any Gemini model. Check your API key and model access. Error: {e_fallback}")
        sys.exit(1)

# --- File Context Configuration ---
FOLDER_PATH = os.path.abspath("../Fact_Checker")  # Use absolute path for robustness
ALLOWED_EXTENSIONS = ('.py', '.md', '.txt', '.js', '.html', '.css', '.json')

# --- Agent Prompt Template ---
AGENT_PROMPT_TEMPLATE = textwrap.dedent("""
    You are an expert code editor and reviewer.
    Your task is to analyze the provided file content, identify potential bugs,
    suggest refactorings for clarity or efficiency, and improve code quality.
    You MUST return the ENTIRE, MODIFIED FILE CONTENT within a single markdown code block.
    If no changes are needed, return the original file content.
    The response MUST be a single markdown code block (e.g., ```python\n...code...\n```)
    containing the complete file content, with no additional text outside the code block.

    ---
    File Path: {filepath}
    File Content:
    ```{file_extension_hint}
    {file_content}
    ```
    ---
    Your Review/Suggestions (return the full modified file here):
""")

# --- Helper Function to Extract Code Block ---
def extract_code_block(response_text: str, filepath: str) -> str | None:
    lines = response_text.strip().split('\n')
    _, ext = os.path.splitext(filepath)
    lang_hint_map = {
        '.py': 'python', '.js': 'javascript', '.html': 'html',
        '.css': 'css', '.json': 'json', '.md': 'markdown', '.txt': 'text'
    }
    expected_lang_hint = lang_hint_map.get(ext.lower(), '')

    if not lines:
        return None

    if lines[0].strip().startswith('```'):
        if len(lines[0].strip()) > 3:
            actual_lang_hint = lines[0].strip()[3:].strip()
            if expected_lang_hint and actual_lang_hint.lower() != expected_lang_hint:
                logging.warning(f"Code block language hint '{actual_lang_hint}' does not match expected '{expected_lang_hint}' for {filepath}.")

        if len(lines) > 1 and lines[-1].strip() == '```':
            return '\n'.join(lines[1:-1])
        else:
            logging.warning(f"Code block for {filepath} not properly closed. Returning full response.")
            return response_text
    else:
        logging.warning(f"Response for {filepath} does not start with a markdown code block. Returning full response.")
        return response_text

# --- Main Logic ---
def process_files_with_gemini():
    if not os.path.exists(FOLDER_PATH):
        logging.critical(f"Folder '{FOLDER_PATH}' not found. Please create it and add files, or update FOLDER_PATH.")
        sys.exit(1)

    logging.info(f"\nProcessing files in '{FOLDER_PATH}' with Gemini")
    processed_count = 0
    for root, _, files in os.walk(FOLDER_PATH):
        for file_name in files:
            if file_name.lower().endswith(ALLOWED_EXTENSIONS):
                filepath = os.path.join(root, file_name)
                logging.info(f"\nAnalyzing file: {filepath}")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    _, ext = os.path.splitext(file_name)
                    file_extension_hint = ext[1:] if ext else ''

                    prompt = AGENT_PROMPT_TEMPLATE.format(
                        filepath=filepath,
                        file_extension_hint=file_extension_hint,
                        file_content=file_content
                    )

                    response = model.generate_content(prompt)

                    if response.text:
                        modified_content = extract_code_block(response.text.strip(), filepath)
                        if modified_content is not None:
                            backup_filepath = filepath + ".bak"
                            shutil.copyfile(filepath, backup_filepath)
                            logging.info(f"Created backup: {backup_filepath}")
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(modified_content)
                            logging.info(f"File '{filepath}' updated successfully.")
                        else:
                            logging.error(f"Could not extract code block from Gemini's response for {filepath}. File not modified.")
                    else:
                        logging.error("Gemini did not return a text response. File not modified.")
                    processed_count += 1
                except FileNotFoundError:
                    logging.warning(f"File not found: {filepath}")
                except UnicodeDecodeError:
                    logging.warning(f"Could not read file '{filepath}' due to encoding error. Skipping.")
                except Exception as e:
                    logging.exception(f"An unexpected error occurred while processing '{filepath}': {e}")
                logging.info("-" * 50)

    if processed_count == 0:
        logging.info(f"\nNo allowed files found in '{FOLDER_PATH}' to process.")
    else:
        logging.info(f"\nFinished processing {processed_count} files.")

if __name__ == "__main__":
    process_files_with_gemini()