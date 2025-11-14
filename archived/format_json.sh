#!/bin/bash

# Script to format/pretty-print JSON files with proper indentation
# Usage: ./format_json.sh

DATA_DIR="./data"

echo "🎨 Formatting JSON files..."

# Format each JSON file with Python's json.tool (4-space indentation)
for file in "$DATA_DIR"/*.json; do
    if [ -f "$file" ]; then
        echo "  Formatting $(basename "$file")..."
        python3 -m json.tool "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
    fi
done

echo "✅ All JSON files formatted with proper indentation"
echo ""
echo "File sizes:"
wc -l "$DATA_DIR"/*.json
