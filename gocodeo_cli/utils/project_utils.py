# gocodeo_cli/utils/project_utils.py

import os
from pathlib import Path
from typing import List, Set

def generate_project_tree(directory_path: str, exclude_dirs: Set[str] = None) -> str:
    """
    Generate a tree representation of the project directory structure.
    
    Args:
        directory_path: The path to the project directory
        exclude_dirs: Set of directory names to exclude (e.g., node_modules, .next)
        
    Returns:
        String representation of the project structure as a tree
    """
    if exclude_dirs is None:
        exclude_dirs = {'node_modules', '.next', '.git', '__pycache__', 'dist', 'build', 'out'}
        
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        return f"Directory not found: {directory_path}"
    
    # Get the project root directory name
    root_name = directory.name
    
    # Initialize the tree with the root directory
    tree_lines = [root_name + "/"]
    
    def _generate_tree(dir_path: Path, prefix: str, is_last: bool, level: int) -> None:
        # Get all files and directories in the current directory, sorted
        # Sort directories first, then files
        items = sorted(list(dir_path.iterdir()), 
                       key=lambda p: (not p.is_dir(), p.name.lower()))
        
        # Count items that will be displayed (excluding those in exclude_dirs)
        visible_items = [item for item in items 
                         if not (item.is_dir() and item.name in exclude_dirs)]
        
        # Process each item
        for i, item in enumerate(visible_items):
            # Determine if this is the last item in the current level
            is_item_last = (i == len(visible_items) - 1)
            
            # Create the prefix for the current item
            if is_last:
                current_prefix = prefix + "    "
            else:
                current_prefix = prefix + "│   "
                
            # Add the item to the tree
            if is_item_last:
                connection = "└── "
            else:
                connection = "├── "
                
            # Add the item to the tree_lines
            if item.is_dir() and item.name not in exclude_dirs:
                tree_lines.append(f"{prefix}{connection}{item.name}/")
                # Recursively process subdirectory
                _generate_tree(item, current_prefix, is_item_last, level + 1)
            elif not item.is_dir():
                # For files, add size information
                tree_lines.append(f"{prefix}{connection}{item.name}")
    
    # Generate the tree starting from the root
    _generate_tree(directory, "", True, 0)
    
    # Convert the list of lines to a string
    return "\n".join(tree_lines)