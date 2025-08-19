# Counting Dataset

A Blender-based pipeline for generating synthetic counting datasets through physics simulation and multi-view rendering.

## Overview

This pipeline processes 3D object datasets to create realistic counting scenarios by:
1. **Cleaning** - Filtering objects to ensure they are watertight and single components
2. **Physics simulation** - Dropping objects into containers to create natural arrangements
3. **Rendering** - Generating multi-view images of the simulated scenes
4. **Assembly** - Collecting all outputs into organized datasets

## Usage

### Step 1: Dataset Cleaning
⚠️ **Warning**: This step permanently removes files from the dataset
```bash
blender --background --python dataset_cleaning.py -- -p "path/to/dataset" -v
```
**Arguments:**
- `-p, --path`: Dataset path (required)
- `-v, --verbose`: Enable verbose output

### Step 2: Physics Simulation
```bash
blender -b --python physics_sim.py -- -p "path/to/dataset" -s 0 -e 100
```
**Arguments:**
- `-p, --path`: Dataset path (required)
- `-s, --start`: Start index (optional)
- `-e, --end`: End index (optional)

### Step 3: Multi-View Rendering
```bash
blender Multi-view-rendering.blend -b --python render.py -- -p "path/to/dataset" -s 0 -e 100
```
**Arguments:**
- `-p, --path`: Dataset path (required)
- `-s, --start`: Start index (optional)
- `-e, --end`: End index (optional)
- `--single_cam`: Render only top view (optional)

### Step 4: Data Assembly
```bash
python assemble_data.py
```
Gathers all pipeline outputs into organized folders. See script for configuration options.

## Project Structure

```
├── source/             # Core classes and utilities
│   ├── BatchPhysicsObject.py
│   ├── Containers.py
│   ├── PhysicsObject.py
│   ├── Scene.py
│   └── Utils.py
├── assets/             # Dataset folder and container models
│   └──dataset/
│      ├──000001/
│      │  └──000001.obj
│      └──000002/
│         └──000002.obj
├── *.blend             # Blender scene files
└── *.py               # Pipeline scripts
```

## Requirements

- Blender 4.3.2+
- coacd 1.0.5+

## Setup

### Installing Blender Packages

You'll need the `coacd` package in Blender:

1. Find Blender's modules path in Blender's Python console:
   ```python
   bpy.utils.user_resource("SCRIPTS", path="modules")
   ```

2. Install packages from terminal:
   ```bash
   pip install coacd --target="path/from/previous/step"
   ```

3. Restart Blender

### Troubleshooting

**NumPy Import Error**: If installing coacd breaks numpy, install without dependencies:
```bash
pip install coacd --no-deps --target='/path/to/blender/modules'
```

