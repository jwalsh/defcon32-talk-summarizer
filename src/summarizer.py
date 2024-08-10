import os
import requests
import json
import tempfile
from typing import List, Dict, Any
import click
from PyPDF2 import PdfReader
from pydantic import BaseModel, ValidationError
import logging
import cohere

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Debug mode: All intermediage data will be logged to logs/debug.log a related file given the source code
global debug_mode 
debug_mode = False

class TalkContent(BaseModel):
    text: str
    metadata: Dict[str, Any] = {}

class Summary(BaseModel):
    title: str
    main_points: List[str]
    technical_details: List[str]
    implications: List[str]

def read_template(file_path: str) -> str:
    """Read the content of a template file."""
    with open(file_path, 'r') as file:
        return file.read()

def read_pdf(file_path: str) -> TalkContent:
    """Extract text content from a PDF file with error handling."""
    try:
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            text = ""
            metadata = {}
            for page in reader.pages:
                text += page.extract_text() + "\n"
            metadata = reader.metadata or {}
        logger.debug(f"Successfully read PDF: {file_path}")
        logger.debug(f"Extracted text length: {len(text)}")
        logger.debug(f"Metadata: {metadata}")
        return TalkContent(text=text, metadata=metadata)
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        return TalkContent(text="", metadata={})

def get_cohere_summary(content: TalkContent, prompt_template: str) -> Summary:
    """Generate a summary using the Cohere API."""
    api_key = os.getenv('COHERE_API_KEY')
    if not api_key:
        raise ValueError("COHERE_API_KEY environment variable is not set")

    co = cohere.Client(api_key)
    prompt = prompt_template.replace("{{CONTENT}}", content.text)

    response = co.generate(
        model='command',
        prompt=prompt,
        max_tokens=300,
        temperature=0.7,
        k=0,
        stop_sequences=[],
        return_likelihoods='NONE'
    )

    # Parse the generated text into our Summary structure
    generated_text = response.generations[0].text
    lines = generated_text.split('\n')
    
    title = lines[0] if lines else "Untitled"
    main_points = [line.strip('- ') for line in lines if line.startswith('- ')][:3]
    technical_details = [line.strip('* ') for line in lines if line.startswith('*')][:2]
    implications = [line for line in lines if 'implication' in line.lower()][:2]

    return Summary(
        title=title,
        main_points=main_points,
        technical_details=technical_details,
        implications=implications
    )

def get_ollama_summary(content: TalkContent, prompt_template: str) -> Summary:
    """Generate a summary using the Ollama API."""
    url = "http://localhost:11434"
    url_generator = f"{url}/api/generate"
    # Check if the Ollama API is running
    if requests.get(url).status_code != 200:
        raise ValueError("Ollama API is not running")
    if debug_mode:
        logger.debug(f"Ollama API is running at: {url}")
    
    payload = {
        "model": "llama3.1:latest",
        "prompt": prompt_template.replace("{{CONTENT}}", content.text),
        "stream": False
    }
    if debug_mode:
        logger.debug(f"Payload: {payload}")
    
    try:
        response = requests.post(url_generator, json=payload)
        response.raise_for_status()
        summary_dict = json.loads(response.json()['response'])
        logger.debug(f"Successfully generated summary: {summary_dict}")
        return Summary(**summary_dict)
    except (requests.RequestException, ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Error generating or validating summary: {str(e)}")
        return Summary(title="Error", main_points=[], technical_details=[], implications=[])

def get_openai_summary(content: TalkContent, prompt_template: str) -> Summary:
    """Generate a summary using the OpenAI API."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    openai.api_key = api_key
    prompt = prompt_template.replace("{{CONTENT}}", content.text)

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=300,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Parse the generated text into our Summary structure
    generated_text = response.choices[0].text.strip()
    lines = generated_text.split('\n')
    
    title = lines[0] if lines else "Untitled"
    main_points = [line.strip('- ') for line in lines if line.startswith('- ')][:3]
    technical_details = [line.strip('* ') for line in lines if line.startswith('*')][:2]
    implications = [line for line in lines if 'implication' in line.lower()][:2]

    return Summary(
        title=title,
        main_points=main_points,
        technical_details=technical_details,
        implications=implications
    )

def get_claude_summary(content: TalkContent, prompt_template: str) -> Summary:
    """Generate a summary using the Anthropic Claude API."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    anthropic = Anthropic(api_key=api_key)
    prompt = prompt_template.replace("{{CONTENT}}", content.text)

    response = anthropic.completions.create(
        model="claude-2",
        prompt=f"{HUMAN_PROMPT}{prompt}{AI_PROMPT}",
        max_tokens_to_sample=300,
    )

    # Parse the generated text into our Summary structure
    generated_text = response.completion
    lines = generated_text.split('\n')
    
    title = lines[0] if lines else "Untitled"
    main_points = [line.strip('- ') for line in lines if line.startswith('- ')][:3]
    technical_details = [line.strip('* ') for line in lines if line.startswith('*')][:2]
    implications = [line for line in lines if 'implication' in line.lower()][:2]

    return Summary(
        title=title,
        main_points=main_points,
        technical_details=technical_details,
        implications=implications
    )

def get_summary_function(provider: str):
    """Factory function to return the appropriate summary function based on the provider."""
    providers = {
        'cohere': get_cohere_summary,
        'ollama': get_ollama_summary,
        'openai': get_openai_summary,
        'claude': get_claude_summary,
    }
    return providers.get(provider, get_cohere_summary)

def process_talk_pdfs(pdf_dir: str, output_dir: str, prompt_template: str, no_summary: bool, provider: str) -> None:
    """Process all PDF files in a directory, generate summaries, and save them."""
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            logger.info(f"Processing file: {pdf_path}")
            content = read_pdf(pdf_path)
            if debug_mode:
                logger.debug(f"PDF content: {content}")

            if content.text:
                if no_summary:
                    logger.info(f"Skipping summary generation for {filename} (--no-summary flag is set)")
                    continue

                prompt = prompt_template.replace("{{CONTENT}}", content.text) # Generated by each provider but here for debugging
                if debug_mode: # Log just the last 40 lines of the prompt for debugging
                    logger.debug(f"Prompt: {prompt[-40:]}")

                summary = get_summary_function(provider)(content, prompt_template)
                if debug_mode:
                    logger.debug(f"Generated summary: {summary}")

                output_filename = os.path.splitext(filename)[0] + '_summary.json'
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, 'w') as file:
                    json.dump(summary.dict(), file, indent=2)
                
                logger.info(f"Processed and saved summary for: {filename}")
            else:
                logger.warning(f"Skipped processing {filename} due to errors")

@click.command()
@click.option('--pdf-dir', default="data/", help="Directory containing mirrored DEF CON 32 talk PDFs")
@click.option('--template-path', default='prompt_defcon_talk_summary_pqrst.tmpl', help="Path to the prompt template file")
@click.option('--output-dir', default='summaries/', help="Directory to save the summaries")
@click.option('--no-summary', is_flag=True, help="Run without generating summaries (for debugging)")
@click.option('--debug', is_flag=True, help="Run without generating summaries (for debugging)")
@click.option('--provider', default='cohere', type=click.Choice(['cohere', 'ollama', 'openai', 'claude']), help="AI provider to use for summarization")
def main(pdf_dir: str, template_path: str, output_dir: str, no_summary: bool, debug: bool, provider: str):
    """Process DEF CON 32 talk PDFs and generate summaries."""
    logger.info("Starting PDF processing" + (" (Debug mode: No summaries will be generated)" if no_summary else ""))
    
    logger.debug(f"PDF directory: {os.path.abspath(pdf_dir)}")
    logger.debug(f"Template path: {os.path.abspath(template_path)}")
    logger.debug(f"Output directory: {os.path.abspath(output_dir)}")

    if debug:
        logger.info("Debug mode enabled")
        global debug_mode
        debug_mode = True
    
    if not os.path.exists(pdf_dir):
        logger.error(f"Input directory {pdf_dir} does not exist.")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(template_path):
        logger.error(f"Template file {template_path} does not exist.")
        return
    
    prompt_template = read_template(template_path)
    logger.debug(f"Prompt template length: {len(prompt_template)}")
    if debug_mode:
        logger.debug(f"Prompt template: {prompt_template}")
    process_talk_pdfs(pdf_dir, output_dir, prompt_template, no_summary, provider)
    
    if not no_summary:
        logger.info(f"All summaries have been saved to: {output_dir}")
    else:
        logger.info("Completed PDF processing without generating summaries.")

if __name__ == "__main__":
    main()
