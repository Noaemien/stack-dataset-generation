#!/bin/bash

# Pipeline script to run the complete counting dataset generation pipeline

usage() {
    echo "Usage: $0 [-a] [-r] [-s] [-c] [-p path]"
    echo "  -a: Run all steps (clean, simulation, rendering)"
    echo "  -r: Run rendering only"
    echo "  -s: Run simulation only"
    echo "  -c: Run cleaning only"
    echo "  -p: Specify dataset path (required)"
    echo "  -h: Display this help message"
    exit 1
}

RUN_ALL=false
RUN_RENDER=false
RUN_SIM=false
RUN_CLEAN=false
DATASET_PATH=""

while getopts "arschp:" opt; do
    case $opt in
        a)
            RUN_ALL=true
            ;;
        r)
            RUN_RENDER=true
            ;;
        s)
            RUN_SIM=true
            ;;
        c)
            RUN_CLEAN=true
            ;;
        p)
            DATASET_PATH="$OPTARG"
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            usage
            ;;
    esac
done

if [ "$RUN_ALL" = false ] && [ "$RUN_RENDER" = false ] && [ "$RUN_SIM" = false ] && [ "$RUN_CLEAN" = false ]; then
    echo "Error: At least one of -a, -r, -s, or -c must be specified."
    usage
fi

if [ -z "$DATASET_PATH" ]; then
    echo "Error: Dataset path must be specified with -p option."
    usage
fi

# Run cleaning step
if [ "$RUN_ALL" = true ] || [ "$RUN_CLEAN" = true ]; then
    echo "=== Running Dataset Cleaning ==="
    blender --background --python dataset_cleaning.py -- -p "$DATASET_PATH" -v
fi

# Run simulation step
if [ "$RUN_ALL" = true ] || [ "$RUN_SIM" = true ]; then
    echo "=== Running Physics Simulation ==="
    blender -b --python physics_sim.py -- -p "$DATASET_PATH" --end 1
fi

# Run rendering step
if [ "$RUN_ALL" = true ] || [ "$RUN_RENDER" = true ]; then
    echo "=== Running Multi-View Rendering ==="
    blender Multi-view-rendering.blend -b --python render.py -- --end 1 -p "$DATASET_PATH"
fi

echo "Pipeline execution completed."
