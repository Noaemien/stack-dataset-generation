
# Just a simple script that copies relevant images to a new shared folder and merges all the json files

import os
import shutil
import json
from concurrent.futures import ThreadPoolExecutor

def process_subfolder(subfolder_path, subfolder, output_folder):
    """Process a single subfolder, check success, and copy required files."""
    result = {
        "subfolder": subfolder,
        "status": "success",
        "copied_files": [],
    }

    json_path = os.path.join(subfolder_path, "simulation_results.json")

    # Check if simulation_results.json exists
    if not os.path.isfile(json_path):
        return "no_simulation"

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        if not data.get("success", False):  # Ensure "success" key exists
            return "simul_failure"

        # Copy RGB file if it exists
        file_suffix = "RGB0011.png"
        src = os.path.join(subfolder_path, "MultiView", "RGB", file_suffix)
        dst = os.path.join(output_folder, f"{subfolder}_{file_suffix}")

        if os.path.isfile(src):
            shutil.copy(src, dst)
            result["copied_files"].append(dst)
            return result
        else:
            return "render_failure"

    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error processing {subfolder}: {e}")
        return "simul_failure"

def process_folder(input_folder, output_folder):
    """Processes multiple subfolders in parallel to improve speed."""
    os.makedirs(output_folder, exist_ok=True)
    combined_results = {}

    success_count = 0
    no_simul_count = 0
    simul_failure_count = 0
    render_failure_count = 0

    subfolders = [f for f in sorted(os.listdir(input_folder)) if os.path.isdir(os.path.join(input_folder, f))]

    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=8) as executor:  # Adjust workers as needed
        results = executor.map(lambda subfolder: process_subfolder(os.path.join(input_folder, subfolder), subfolder, output_folder), subfolders)

    successes = []
    # Process results
    for res in results:
        if isinstance(res, dict):
            success_count += 1
            combined_results[res["subfolder"]] = res
            successes.append(res["subfolder"])
        elif res == "no_simulation":
            no_simul_count += 1
        elif res == "simul_failure":
            simul_failure_count += 1
        elif res == "render_failure":
            render_failure_count += 1

    # Write combined JSON results
    with open(os.path.join(output_folder, "combined_results.json"), 'w') as f:
        json.dump(combined_results, f, indent=4)

        
    #print(successes)
        
    # Print stats
    print("Simulation success:")
    print(f"\t# with renders:    {success_count}")
    print(f"\t# of fail render:   {render_failure_count}")
    
    print("\nSimulation fail:")
    print(f"\t# of no sim:   {no_simul_count}")
    print(f"\t# of fail sim:   {simul_failure_count}")
    
    print(f"\nSimulation:  {100 *(success_count + render_failure_count) / (success_count + render_failure_count + no_simul_count + simul_failure_count):.2f}%")
    if success_count + render_failure_count > 0:
        print(f"Rendering :  {100 *(success_count) / (success_count + render_failure_count)}%")

# Run the function
process_folder("assets/abc_5", "assets/dataset5")
