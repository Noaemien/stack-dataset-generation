#!/bin/bash

# Script to clear ACD (Approximate Convex Decomposition) cache files

BASE_DIR="assets/containers"

usage() {
    echo "Usage: $0 [-d directory] [-h]"
    echo "  -d: Specify base directory (default: assets/containers)"
    echo "  -h: Display this help message"
    exit 1
}

while getopts "d:h" opt; do
    case $opt in
        d)
            BASE_DIR="$OPTARG"
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
    esac
done

if [ ! -d "$BASE_DIR" ]; then
    echo "Error: Directory $BASE_DIR does not exist."
    exit 1
fi

deleted_count=0

for dir in "$BASE_DIR"/*/; do
    if [ -d "$dir" ]; then  
        file="$dir/acd_data.npz"
        if [ -f "$file" ]; then
            echo "Deleting: $file"
            rm "$file"
            ((deleted_count++))
        else
            echo "No acd_data.npz found in $dir"
        fi
    fi
done

echo "Done. Deleted $deleted_count files."
