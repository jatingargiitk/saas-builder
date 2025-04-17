"""
Service for managing project state throughout the agentic development process.
"""
import json
import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

class ProjectStage(Enum):
    """Enum representing the current stage of project development."""
    INITIALIZED = "initialized"
    UI_GENERATED = "ui_generated"
    AUTH_ADDED = "auth_added"
    DATA_ADDED = "data_added"
    FEATURES_ADDED = "features_added"
    COMPLETED = "completed"

class ProjectState:
    """Manages the state of a project throughout its development lifecycle."""
    
    def __init__(self, project_dir: Path):
        """
        Initialize the project state manager.
        
        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = project_dir
        self.state_file = project_dir / ".gocodeo" / "state.json"
        self._state = {
            "name": "",
            "description": "",
            "tech_stack": "",
            "model": "",
            "stage": ProjectStage.INITIALIZED.value,
            "features": [],
            "history": [],
            "ui_components": [],
            "data_models": [],
            "files": {}
        }
        
        # Create .gocodeo directory if it doesn't exist
        (project_dir / ".gocodeo").mkdir(parents=True, exist_ok=True)
        
        # Load existing state if it exists
        if self.state_file.exists():
            self._load_state()
    
    def _load_state(self):
        """Load project state from the state file."""
        try:
            with open(self.state_file, "r") as f:
                self._state = json.load(f)
        except Exception as e:
            print(f"Failed to load project state: {str(e)}")
    
    def _save_state(self):
        """Save project state to the state file."""
        with open(self.state_file, "w") as f:
            json.dump(self._state, f, indent=2)
    
    def initialize(self, name: str, description: str, tech_stack: str, model: str):
        """
        Initialize a new project.
        
        Args:
            name: Project name
            description: Project description
            tech_stack: Selected tech stack
            model: LLM model to use
        """
        self._state["name"] = name
        self._state["description"] = description
        self._state["tech_stack"] = tech_stack
        self._state["model"] = model
        self._state["stage"] = ProjectStage.INITIALIZED.value
        self._state["history"].append({
            "stage": ProjectStage.INITIALIZED.value,
            "timestamp": get_timestamp(),
            "action": "Project initialized"
        })
        self._save_state()
    
    def update_stage(self, stage: ProjectStage):
        """
        Update the current stage of the project.
        
        Args:
            stage: New project stage
        """
        self._state["stage"] = stage.value
        self._state["history"].append({
            "stage": stage.value,
            "timestamp": get_timestamp(),
            "action": f"Updated stage to {stage.value}"
        })
        self._save_state()
    
    def add_ui_component(self, component: Dict[str, Any]):
        """
        Add a UI component to the project.
        
        Args:
            component: UI component definition
        """
        self._state["ui_components"].append(component)
        self._state["history"].append({
            "stage": self._state["stage"],
            "timestamp": get_timestamp(),
            "action": f"Added UI component: {component.get('name', 'Unnamed')}"
        })
        self._save_state()
    
    def add_data_model(self, model: Dict[str, Any]):
        """
        Add a data model to the project.
        
        Args:
            model: Data model definition
        """
        self._state["data_models"].append(model)
        self._state["history"].append({
            "stage": self._state["stage"],
            "timestamp": get_timestamp(),
            "action": f"Added data model: {model.get('name', 'Unnamed')}"
        })
        self._save_state()
    
    def add_feature(self, feature: str):
        """
        Add a feature to the project.
        
        Args:
            feature: Feature name
        """
        if feature not in self._state["features"]:
            self._state["features"].append(feature)
            self._state["history"].append({
                "stage": self._state["stage"],
                "timestamp": get_timestamp(),
                "action": f"Added feature: {feature}"
            })
            self._save_state()
    
    def add_files(self, files: Dict[str, str]):
        """
        Add generated files to the project state.
        
        Args:
            files: Dictionary mapping file paths to their contents
        """
        for file_path, content in files.items():
            self._state["files"][file_path] = {
                "added_at": get_timestamp(),
                "stage": self._state["stage"],
                "modified": False
            }
        self._save_state()
    
    def get_current_stage(self) -> ProjectStage:
        """
        Get the current stage of the project.
        
        Returns:
            Current project stage
        """
        return ProjectStage(self._state["stage"])
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get basic project information.
        
        Returns:
            Dictionary with project information
        """
        return {
            "name": self._state["name"],
            "description": self._state["description"],
            "tech_stack": self._state["tech_stack"],
            "model": self._state["model"],
            "stage": self._state["stage"],
            "features": self._state["features"]
        }
    
    def get_full_state(self) -> Dict[str, Any]:
        """
        Get the full project state.
        
        Returns:
            Complete project state
        """
        return self._state
    
    def can_proceed_to_stage(self, stage: ProjectStage) -> bool:
        """
        Check if the project can proceed to the specified stage.
        
        Args:
            stage: Target stage
        
        Returns:
            True if the project can proceed to the specified stage
        """
        current_stage = self.get_current_stage()
        
        # Define valid stage progressions
        valid_progressions = {
            ProjectStage.INITIALIZED: [ProjectStage.UI_GENERATED,ProjectStage.AUTH_ADDED,ProjectStage.DATA_ADDED],
            ProjectStage.UI_GENERATED: [ProjectStage.AUTH_ADDED],
            ProjectStage.AUTH_ADDED: [ProjectStage.DATA_ADDED],
            ProjectStage.DATA_ADDED: [ProjectStage.FEATURES_ADDED, ProjectStage.COMPLETED],
            ProjectStage.FEATURES_ADDED: [ProjectStage.COMPLETED],
            ProjectStage.COMPLETED: []
        }
        
        return stage in valid_progressions.get(current_stage, [])
    def get_files(self) -> list:
        """
        Get the list of files in the project.
        
        Returns:
            List of file paths relative to the project directory
        """
        # If state has 'files' as a dictionary of {filepath: timestamp}, extract keys
        if isinstance(self._state.get('files', {}), dict):
            return list(self._state.get('files', {}).keys())
        # If state has 'files' as a list, return it directly
        return self._state.get('files', [])

def get_timestamp() -> str:
    """
    Get the current timestamp in ISO format.
    
    Returns:
        Current timestamp as string
    """
    from datetime import datetime
    return datetime.now().isoformat()

def load_project_state(project_dir: Path) -> ProjectState:
    """
    Load the project state for the specified directory.
    
    Args:
        project_dir: Path to the project directory
    
    Returns:
        ProjectState instance
    """
    return ProjectState(project_dir) 