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

def process_talk_pdfs(pdf_dir: str, output_dir: str, prompt_template: str, no_summary: bool) -> None:
    """Process all PDF files in a directory, generate summaries, and save them."""
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            logger.info(f"Processing file: {pdf_path}")
            content = read_pdf(pdf_path)
            
            if content.text:
                if no_summary:
                    logger.info(f"Skipping summary generation for {filename} (--no-summary flag is set)")
                    continue
                
                summary = get_cohere_summary(content, prompt_template)
                
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
def main(pdf_dir: str, template_path: str, output_dir: str, no_summary: bool):
    """Process DEF CON 32 talk PDFs and generate summaries."""
    logger.info("Starting PDF processing" + (" (Debug mode: No summaries will be generated)" if no_summary else ""))
    
    logger.debug(f"PDF directory: {os.path.abspath(pdf_dir)}")
    logger.debug(f"Template path: {os.path.abspath(template_path)}")
    logger.debug(f"Output directory: {os.path.abspath(output_dir)}")
    
    if not os.path.exists(pdf_dir):
        logger.error(f"Input directory {pdf_dir} does not exist.")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(template_path):
        logger.error(f"Template file {template_path} does not exist.")
        return
    
    prompt_template = read_template(template_path)
    logger.debug(f"Prompt template length: {len(prompt_template)}")
    
    process_talk_pdfs(pdf_dir, output_dir, prompt_template, no_summary)
    
    if not no_summary:
        logger.info(f"All summaries have been saved to: {output_dir}")
    else:
        logger.info("Completed PDF processing without generating summaries.")

if __name__ == "__main__":
    main()
