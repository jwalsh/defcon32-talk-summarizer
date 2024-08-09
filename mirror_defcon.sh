#!/bin/bash
# mirror_defcon.sh
# Mirrors the DEF CON 32 media archive

if [ -z "$(which wget)" ]; then
	echo "Error: wget is not installed"
	exit 1
fi

# Check if we're getting a different mirror directory
MIRROR_DIR="defcon32-media"
if [ ! -z "$1" ]; then
	MIRROR_DIR="$1"
fi

mkdir -p "$MIRROR_DIR"

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
     https://media.defcon.org/DEF%20CON%2032/

echo "Mirroring complete. Content saved in $MIRROR_DIR"
