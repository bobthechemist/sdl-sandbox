#!/usr/bin/env python3
import argparse
import datetime
import sys
from pathlib import Path

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Generates a Markdown snippet of the codebase for agentic firmware design."
    )
    parser.add_argument(
        "firmware", 
        help="Name of the target firmware directory (e.g., sidekick, colorimeter)"
    )
    args = parser.parse_args()

    # Resolve project root assuming this script is in <root>/utility/
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define target directories to include
    target_dirs = [
        project_root / "shared_lib",
        project_root / "firmware" / "common",
        project_root / "firmware" / args.firmware
    ]

    # Validate that all required directories exist
    for d in target_dirs:
        if not d.exists() or not d.is_dir():
            print(f"Error: Required directory does not exist: {d.relative_to(project_root)}")
            sys.exit(1)

    # Setup the temp output directory and file
    temp_dir = project_root / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    date_str = datetime.datetime.now().strftime("%y%m%d")
    output_filename = f"code_context_{date_str}.md"
    output_path = temp_dir / output_filename

    print(f"Gathering Python files into {output_filename}...")

    # Write contents to the markdown file
    with open(output_path, "w", encoding="utf-8") as out_file:
        for target_dir in target_dirs:
            # Recursively find all .py files and sort them for consistent output
            py_files = sorted(target_dir.rglob("*.py"))
            
            if not py_files:
                continue

            current_dir_printed = None

            for py_file in py_files:
                # Get the relative path of the parent directory (e.g., "firmware/sidekick")
                # Using as_posix() to ensure forward slashes regardless of the OS
                rel_dir = py_file.parent.relative_to(project_root).as_posix()
                
                # Print the Directory header only when the directory changes
                if current_dir_printed != rel_dir:
                    out_file.write(f"## Directory {rel_dir}\n\n")
                    current_dir_printed = rel_dir
                
                # Print File header and contents
                out_file.write(f"### {py_file.name}\n\n")
                out_file.write("```python\n")
                
                try:
                    content = py_file.read_text(encoding="utf-8")
                    out_file.write(content)
                    
                    # Ensure there is a trailing newline before closing the codeblock
                    if not content.endswith("\n"):
                        out_file.write("\n")
                except Exception as e:
                    out_file.write(f"# Error reading file: {e}\n")
                
                out_file.write("```\n\n")

    print(f"Success! Context generated at: {output_path.relative_to(project_root)}")

if __name__ == "__main__":
    main()