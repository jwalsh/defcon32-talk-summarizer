import os
import requests
import json
import tempfile
from typing import List, Dict, Any
import click
from PyPDF2 import PdfReader
from pydantic import BaseModel, ValidationError

class TalkContent(BaseModel):
    text: str
    metadata: Dict[str, Any]

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
            metadata = reader.metadata
        return TalkContent(text=text, metadata=metadata)
    except Exception as e:
        print(f"Error processing PDF {file_path}: {str(e)}")
        return TalkContent(text="", metadata={})

def get_ollama_summary(content: TalkContent, prompt_template: str) -> Summary:
    """Generate a summary using the Ollama API with type validation."""
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "llama2",
        "prompt": prompt_template.replace("{{CONTENT}}", content.text),
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        summary_dict = json.loads(response.json()['response'])
        return Summary(**summary_dict)
    except (requests.RequestException, ValidationError, json.JSONDecodeError) as e:
        print(f"Error generating or validating summary: {str(e)}")
        return Summary(title="Error", main_points=[], technical_details=[], implications=[])

def process_talk_pdfs(pdf_dir: str, output_dir: str, prompt_template: str) -> None:
    """Process all PDF files in a directory, generate summaries, and save them."""
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            content = read_pdf(pdf_path)

            if content.text:
                summary = get_ollama_summary(content, prompt_template)

                output_filename = os.path.splitext(filename)[0] + '_summary.json'
                output_path = os.path.join(output_dir, output_filename)

                with open(output_path, 'w') as file:
                    json.dump(summary.dict(), file, indent=2)

                print(f"Processed and saved summary for: {filename}")
            else:
                print(f"Skipped processing {filename} due to errors")

@click.command()
@click.option('--pdf-dir', required=True, help="Directory containing mirrored DEF CON 32 talk PDFs")
@click.option('--template-path', default='prompt_defcon_talk_summary_pqrst.tmpl', help="Path to the prompt template file")
@click.option('--output-dir', default=None, help="Directory to save the summaries (defaults to a temporary directory)")
def main(pdf_dir: str, template_path: str, output_dir: str):
    """Process DEF CON 32 talk PDFs and generate summaries."""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        process_summaries(pdf_dir, output_dir, template_path)
    else:
        with tempfile.TemporaryDirectory(prefix="defcon32_summaries_") as temp_dir:
            print(f"Temporary output directory created: {temp_dir}")
            process_summaries(pdf_dir, temp_dir, template_path)
            print("Review the summaries and move them to a permanent location if needed.")

def process_summaries(pdf_dir: str, output_dir: str, template_path: str):
    prompt_template = read_template(template_path)
    process_talk_pdfs(pdf_dir, output_dir, prompt_template)
    print(f"All summaries have been saved to: {output_dir}")

if __name__ == "__main__":
    print("Processing DEF CON 32 talk PDFs and generating summaries...")
