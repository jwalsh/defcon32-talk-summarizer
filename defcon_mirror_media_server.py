#!/usr/bin/env python3

import os
import json
from datetime import datetime, timezone
from typing import List, Optional

import click
import scrapy
from pydantic import BaseModel, HttpUrl
from scrapy.crawler import CrawlerProcess
import markdown
import pypandoc
from pdf2image import convert_from_path
from PIL import Image


class FilterRule(BaseModel):
    """Represents a filter rule for content mirroring."""
    name: str
    description: str


class ScrapyOptions(BaseModel):
    """Represents Scrapy-specific options for the mirror process."""
    user_agent: str = "DEF CON 32 Content Mirror"
    download_delay: float = 1.0
    randomize_download_delay: bool = True


class PostProcessingOptions(BaseModel):
    """Represents post-processing options for mirrored content."""
    to_markdown: bool = False
    to_text: bool = False
    to_png: bool = False
    create_thumbnail: bool = False


class MirrorConfig(BaseModel):
    """Represents the configuration for the mirroring process."""
    source: HttpUrl
    output_directory: str
    filter_rules: List[FilterRule]
    mirror_date: datetime
    force_download: bool
    scrapy_options: ScrapyOptions
    post_processing: PostProcessingOptions


class DefconSpider(scrapy.Spider):
    """Spider for scraping DEF CON 32 presentations."""
    
    name = "defcon"

    def __init__(self, url: str, output_dir: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url]
        self.output_dir = output_dir

    def parse(self, response):
        """Parse the response and yield requests for PDF files."""
        for pdf_link in response.css('a[href$=".pdf"]::attr(href)').getall():
            yield scrapy.Request(url=response.urljoin(pdf_link), callback=self.save_pdf)

    def save_pdf(self, response):
        """Save the PDF file to the output directory."""
        filename = response.url.split('/')[-1]
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.body)
        self.logger.info(f"Saved file {filename}")


def generate_manifest(config: MirrorConfig) -> None:
    """
    Generate a manifest file for the mirroring process.
    
    Args:
        config (MirrorConfig): The configuration for the mirroring process.
    """
    manifest_path = os.path.join(config.output_directory, "manifest.json")
    with open(manifest_path, "w") as f:
        f.write(config.json(indent=2))
    click.echo(f"Manifest file generated at {manifest_path}")


def post_process_content(config: MirrorConfig) -> None:
    """
    Perform post-processing on mirrored content based on specified options.
    
    Args:
        config (MirrorConfig): The configuration for the mirroring process.
    """
    for filename in os.listdir(config.output_directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(config.output_directory, filename)
            base_name = os.path.splitext(filename)[0]

            if config.post_processing.to_markdown:
                md_path = os.path.join(config.output_directory, f"{base_name}.md")
                pypandoc.convert_file(pdf_path, 'md', outputfile=md_path)
                click.echo(f"Generated Markdown: {md_path}")

            if config.post_processing.to_text:
                txt_path = os.path.join(config.output_directory, f"{base_name}.txt")
                pypandoc.convert_file(pdf_path, 'plain', outputfile=txt_path)
                click.echo(f"Generated Text: {txt_path}")

            if config.post_processing.to_png:
                png_path = os.path.join(config.output_directory, f"{base_name}.png")
                images = convert_from_path(pdf_path)
                images[0].save(png_path, 'PNG')
                click.echo(f"Generated PNG: {png_path}")

            if config.post_processing.create_thumbnail:
                thumb_path = os.path.join(config.output_directory, f"{base_name}_thumb.png")
                images = convert_from_path(pdf_path, first_page=1, last_page=1)
                images[0].thumbnail((200, 200))
                images[0].save(thumb_path, 'PNG')
                click.echo(f"Generated Thumbnail: {thumb_path}")


@click.command()
@click.option("--mirror-dir", default="defcon32-media", help="Directory to store mirrored content")
@click.option("--force", is_flag=True, help="Force re-download of existing content")
@click.option("--to-markdown", is_flag=True, help="Convert PDFs to Markdown")
@click.option("--to-text", is_flag=True, help="Convert PDFs to plain text")
@click.option("--to-png", is_flag=True, help="Convert PDFs to PNG images")
@click.option("--create-thumbnail", is_flag=True, help="Create thumbnails for PDFs")
def defcon_mirror_media_server(
    mirror_dir: str,
    force: bool,
    to_markdown: bool,
    to_text: bool,
    to_png: bool,
    create_thumbnail: bool
) -> None:
    """
    Mirror the DEF CON 32 media archive, generate a manifest, and perform post-processing.
    
    Args:
        mirror_dir (str): Directory to store mirrored content.
        force (bool): Whether to force re-download of existing content.
        to_markdown (bool): Convert PDFs to Markdown.
        to_text (bool): Convert PDFs to plain text.
        to_png (bool): Convert PDFs to PNG images.
        create_thumbnail (bool): Create thumbnails for PDFs.
    """
    host = "media.defcon.org"
    presentation_dir = "DEF CON 32/DEF CON 32 presentations"
    url = f"https://{host}/{presentation_dir}"

    if os.path.exists(mirror_dir) and not force:
        click.echo(f"Content already exists in {mirror_dir}")
        click.echo("Use --force to re-download existing content")
        return

    click.echo(f"Mirroring {url} to {mirror_dir}")
    if force:
        click.echo("Force flag is set. Existing content will be overwritten.")

    if not click.confirm("Do you want to continue?"):
        click.echo("Exiting...")
        return

    os.makedirs(mirror_dir, exist_ok=True)

    config = MirrorConfig(
        source=url,
        output_directory=mirror_dir,
        filter_rules=[
            FilterRule(name="pdf_only", description="Only mirror PDF files"),
            FilterRule(name="exclude_index", description="Exclude index.html files"),
            FilterRule(name="respect_robots", description="Respect robots.txt rules"),
        ],
        mirror_date=datetime.now(timezone.utc),
        force_download=force,
        scrapy_options=ScrapyOptions(),
        post_processing=PostProcessingOptions(
            to_markdown=to_markdown,
            to_text=to_text,
            to_png=to_png,
            create_thumbnail=create_thumbnail
        ),
    )

    process = CrawlerProcess({
        'USER_AGENT': config.scrapy_options.user_agent,
        'DOWNLOAD_DELAY': config.scrapy_options.download_delay,
        'RANDOMIZE_DOWNLOAD_DELAY': config.scrapy_options.randomize_download_delay,
    })

    process.crawl(DefconSpider, url=url, output_dir=mirror_dir)
    process.start()

    generate_manifest(config)

    if any([to_markdown, to_text, to_png, create_thumbnail]):
        click.echo("Performing post-processing...")
        post_process_content(config)

    click.echo(f"Mirroring and post-processing complete. Content saved in {mirror_dir}")


if __name__ == "__main__":
    defcon_mirror_media_server()
