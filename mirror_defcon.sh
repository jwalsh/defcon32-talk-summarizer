#!/bin/bash

# mirror_defcon.sh
# Mirrors the DEF CON 32 media archive and generates a manifest

# Global variables
MIRROR_DIR="defcon32-media"
HOST="media.defcon.org"
PRESENTATION_DIR="DEF CON 32/DEF CON 32 presentations"
MANIFEST_FILE="manifest.json"

# Function: defcon_mirror_media_server
# Input: None (uses global variables)
# Output: Downloads and processes PDF files, storing them in MIRROR_DIR
#         Generates a manifest file with source URL, output dir, and filter rules
defcon_mirror_media_server() {
    # Check for wget
    if [ -z "$(which wget)" ]; then
        echo "Error: wget is not installed"
        exit 1
    fi

    # Check if we're getting a different mirror directory
    if [ ! -z "$1" ]; then
        MIRROR_DIR="$1"
    fi

    # Check if this already exists and ask if we want to overwrite
    if [ -d "$MIRROR_DIR/$HOST/$PRESENTATION_DIR" ]; then
        read -p "The directory $MIRROR_DIR/$HOST/$PRESENTATION_DIR already exists. Do you want to overwrite it? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Exiting..."
            exit 1
        fi
    fi

    # Confirm before starting
    echo "Mirroring https://$HOST/$PRESENTATION_DIR to $MIRROR_DIR"
    read -p "Do you want to continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi

    # Create mirror directory
    mkdir -p "$MIRROR_DIR"

    # Download content
    wget --no-check-certificate \
         --mirror \
         --convert-links \
         --adjust-extension \
         --page-requisites \
         --no-parent \
         --directory-prefix="$MIRROR_DIR" \
         --reject "index.html*" \
         --execute robots=on \
         --wait 1 \
         --random-wait \
         --user-agent="DEF CON 32 Content Mirror" \
         "https://$HOST/$PRESENTATION_DIR"

    # Generate manifest
    generate_manifest

    echo "Mirroring complete. Content saved in $MIRROR_DIR"
    echo "Manifest file generated at $MIRROR_DIR/$MANIFEST_FILE"
}

# Function to generate the manifest file
generate_manifest() {
    cat > "$MIRROR_DIR/$MANIFEST_FILE" << EOF
{
    "source": "https://$HOST/$PRESENTATION_DIR",
    "output_directory": "$MIRROR_DIR",
    "filter_rules": [
        {"name": "pdf_only", "description": "Only mirror PDF files"},
        {"name": "exclude_index", "description": "Exclude index.html files"},
        {"name": "respect_robots", "description": "Respect robots.txt rules"}
    ],
    "mirror_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "wget_options": {
        "no_check_certificate": true,
        "mirror": true,
        "convert_links": true,
        "adjust_extension": true,
        "page_requisites": true,
        "no_parent": true,
        "wait": 1,
        "random_wait": true,
        "user_agent": "DEF CON 32 Content Mirror"
    }
}
EOF
}

# Run the main function
defcon_mirror_media_server "$@"
