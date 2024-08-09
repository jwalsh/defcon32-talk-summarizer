# DEF CON 32 Talk Summarizer

This project aims to securely mirror and summarize talks from DEF CON 32 using AI-powered text analysis. It provides a containerized environment for processing PDF documents of conference talks and generating concise summaries.

## Features

- Secure mirroring of DEF CON 32 content
- PDF processing and text extraction
- AI-powered summarization using Ollama API
- Containerized execution for improved security and portability

## Prerequisites

- Docker
- Ollama API running locally (for summarization)

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/defcon32-talk-summarizer.git
   cd defcon32-talk-summarizer
   ```

2. Build the Docker image:
   ```
   docker build -t defcon32-summarizer .
   ```

## Usage

1. Mirror DEF CON 32 content (optional, if you haven't already):
   ```
   docker run -it --rm -v $(pwd)/mirror:/home/appuser/defcon32_mirror defcon32-summarizer --mirror
   ```

2. Run the summarizer:
   ```
   docker run -it --rm \
     -v $(pwd)/mirror:/home/appuser/defcon32_mirror \
     -v $(pwd)/summaries:/home/appuser/summaries \
     defcon32-summarizer \
     --pdf-dir /home/appuser/defcon32_mirror \
     --output-dir /home/appuser/summaries
   ```

   This command will process the PDFs in the mirror directory and save summaries to the summaries directory.

3. Review the generated summaries in the `summaries` directory.

## Configuration

- Modify `prompt_defcon_talk_summary_pqrst.tmpl` to adjust the summarization prompt.
- Update `requirements.txt` if you need to add or modify Python dependencies.

## Contributing

Contributions to improve the DEF CON 32 Talk Summarizer are welcome. Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear, descriptive commit messages.
4. Push your changes to your fork.
5. Submit a pull request with a clear description of your changes.

Please ensure your code adheres to the existing style and passes all tests. Add or update tests as necessary for new features or bug fixes.

## Security Considerations

This tool is designed to process potentially sensitive content. Always review the generated summaries before sharing or publishing them. Ensure you have permission to access and process DEF CON 32 content before using this tool.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is not officially affiliated with DEF CON. Use it responsibly and in accordance with DEF CON's terms of service and any applicable laws or regulations.

## Acknowledgments

- DEF CON for providing the conference content
- Ollama for the AI summarization capabilities
