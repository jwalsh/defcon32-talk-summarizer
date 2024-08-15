import os
import time
from typing import Set, Optional
from urllib.parse import urlparse
import hashlib

import scrapy
from scrapy.http import Response
from scrapy.crawler import CrawlerProcess
from pydantic import BaseModel, HttpUrl
import click

class DefConConfig(BaseModel):
    """Configuration for the DEF CON spider."""
    output_dir: str
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_domains: Set[str] = {"media.defcon.org"}
    start_url: HttpUrl = "https://media.defcon.org/"

class DefConSpider(scrapy.Spider):
    """Spider for comprehensively downloading DEF CON content."""

    name = "comprehensive_defcon"

    def __init__(self, config: DefConConfig):
        """
        Initialize the DEF CON spider.

        Args:
            config (DefConConfig): Configuration for the spider.
        """
        super().__init__()
        self.config = config
        self.allowed_domains = list(config.allowed_domains)
        self.start_urls = [str(config.start_url)]
        self.downloaded_files: Set[str] = set()

    def parse(self, response: Response):
        """
        Parse the main page and follow links to DEF CON events.

        Args:
            response (Response): The response object from the main page.

        Yields:
            scrapy.Request: Requests for DEF CON event pages.
        """
        for link in response.css('a::attr(href)').getall():
            if self.is_allowed_path(link):
                yield response.follow(link, self.parse_event)

    def parse_event(self, response: Response):
        """
        Parse a DEF CON event page and process its content.

        Args:
            response (Response): The response object from an event page.

        Yields:
            scrapy.Request: Requests for file downloads or subdirectories.
        """
        event_name = self.get_event_name(response.url)
        if not event_name:
            return

        for link in response.css('a::attr(href)').getall():
            if self.is_allowed_file(link):
                yield scrapy.Request(
                    response.urljoin(link),
                    callback=self.save_file,
                    meta={'event_name': event_name}
                )
            elif self.is_subdirectory(link):
                yield response.follow(link, self.parse_event)

    def is_allowed_path(self, path: str) -> bool:
        """
        Check if a path is allowed for crawling.

        Args:
            path (str): The path to check.

        Returns:
            bool: True if the path is allowed, False otherwise.
        """
        allowed_paths = [
            'DEF CON ', 'Conference Programs', 'DEF CON Music',
            'DEF CON China', 'DEF CON NYE 2020'
        ]
        return any(allowed in path for allowed in allowed_paths)

    def is_allowed_file(self, filename: str) -> bool:
        """
        Check if a file is allowed for downloading.

        Args:
            filename (str): The filename to check.

        Returns:
            bool: True if the file is allowed, False otherwise.
        """
        allowed_extensions = ['.pdf', '.flac', '.opus', '.txt']
        return any(filename.lower().endswith(ext) for ext in allowed_extensions)

    def is_subdirectory(self, path: str) -> bool:
        """
        Check if a path is a subdirectory.

        Args:
            path (str): The path to check.

        Returns:
            bool: True if the path is a subdirectory, False otherwise.
        """
        return path.endswith('/')

    def get_event_name(self, url: str) -> Optional[str]:
        """
        Extract the event name from a URL.

        Args:
            url (str): The URL to extract the event name from.

        Returns:
            Optional[str]: The event name if found, None otherwise.
        """
        parts = url.split('/')
        for part in parts:
            if part.startswith('DEF CON '):
                return part
        return None

    def save_file(self, response: Response):
        """
        Save a file and update metadata.

        Args:
            response (Response): The response object containing the file.
        """
        event_name = response.meta['event_name']
        filename = os.path.basename(urlparse(response.url).path)
        event_dir = os.path.join(self.config.output_dir, event_name)
        filepath = os.path.join(event_dir, filename)

        if int(response.headers.get('Content-Length', 0)) > self.config.max_file_size:
            self.logger.info(f"Skipping large file: {response.url}")
            return

        file_hash = hashlib.md5(response.body).hexdigest()
        if file_hash in self.downloaded_files:
            self.logger.info(f"Skipping duplicate file: {filename}")
            return

        os.makedirs(event_dir, exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(response.body)
        
        self.downloaded_files.add(file_hash)
        self.logger.info(f"Saved file {filename} to {event_dir}")

        self.update_metadata(event_name, filename)

        time.sleep(1)  # Respectful delay

    def update_metadata(self, event_name: str, filename: str):
        """
        Update the metadata file for an event.

        Args:
            event_name (str): The name of the event.
            filename (str): The name of the file to add to metadata.
        """
        metadata_file = os.path.join(self.config.output_dir, f"{event_name}_metadata.txt")
        with open(metadata_file, 'a') as f:
            f.write(f"{filename}\n")

    def closed(self, reason: str):
        """
        Create a master index when the spider is closed.

        Args:
            reason (str): The reason for closing the spider.
        """
        with open(os.path.join(self.config.output_dir, 'master_index.txt'), 'w') as f:
            for event_dir in os.listdir(self.config.output_dir):
                if os.path.isdir(os.path.join(self.config.output_dir, event_dir)):
                    f.write(f"{event_dir}:\n")
                    for file in os.listdir(os.path.join(self.config.output_dir, event_dir)):
                        f.write(f"  {file}\n")
                    f.write("\n")

@click.command()
@click.option('--output-dir', default='defcon-comprehensive-archive', help='Directory to store the downloaded content')
@click.option('--max-file-size', default=100*1024*1024, help='Maximum file size to download in bytes')
def run_spider(output_dir: str, max_file_size: int):
    """
    Run the DEF CON spider with the specified configuration.

    Args:
        output_dir (str): The directory to store downloaded content.
        max_file_size (int): The maximum file size to download in bytes.
    """
    config = DefConConfig(output_dir=output_dir, max_file_size=max_file_size)
    process = CrawlerProcess({
        'USER_AGENT': 'DEF CON Content Archiver (Educational/Research Use)',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 1,  # Be extra respectful
    })

    process.crawl(DefConSpider, config=config)
    process.start()

if __name__ == "__main__":
    run_spider()
