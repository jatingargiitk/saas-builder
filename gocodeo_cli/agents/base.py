from enum import Enum
from typing import List, Dict, Optional, Any
import json
import os
import re
import logging
from pathlib import Path
from rich.console import Console
import zipfile
from importlib import resources
import io

logger = logging.getLogger(__name__)
console = Console()

class AgentState(str, Enum):
    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    ADDING_AUTH = "ADDING_AUTH"
    ADDING_DATA = "ADDING_DATA"
    FINISHED = "FINISHED"
    ERROR = "ERROR"

class AgentMemory:
    def __init__(self):
        self.messages: List[Dict] = []
        self.context: Dict = {}
        self.files: Dict[str, str] = {}
        
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > 20:  # Keep the memory manageable
            self.messages = self.messages[-20:]
        
    def get_context(self) -> str:
        # Return last few messages as context
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.messages[-5:]])
        
    def update_context(self, key: str, value: any):
        self.context[key] = value
        
    def add_files(self, files: Dict[str, str]):
        self.files.update(files)

class BaseTool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    async def execute(self, agent: 'BaseAgent', **kwargs) -> str:
        """Execute the tool functionality"""
        raise NotImplementedError

class BaseAgent:
    def __init__(self, name: str, project_dir: Path):
        self.name = name
        self.memory = AgentMemory()
        self.tools = {}
        self.console = Console()
        self.project_dir = project_dir
        self.state = AgentState.IDLE
        
    def add_tool(self, tool: BaseTool):
        """Register a tool with the agent"""
        self.tools[tool.name] = tool
        
    def load_prompt_template(self, template_name: str) -> str:
        """Load a prompt template from the templates directory"""
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                    "templates", "prompts", f"{template_name}.txt")
        try:
            with open(template_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise Exception(f"Template {template_name} not found at {template_path}")
            
    # Add to gocodeo_cli/agents/base.py
    def format_prompt(self, template_name: str = None, template_content: str = None, **kwargs) -> str:
        """
        Format a prompt template with variables.
        
        Args:
            template_name: Name of template to load (if template_content is not provided)
            template_content: Raw template content (if provided, overrides template_name)
            **kwargs: Variables to replace in the template
            
        Returns:
            Formatted prompt
        """
        # Get template content either from the provided content or by loading a template file
        if template_content is None:
            if template_name is None:
                raise ValueError("Either template_name or template_content must be provided")
            template_content = self.load_prompt_template(template_name)
        
        # Simple string replacement for each key in kwargs
        formatted_prompt = template_content
        for key, value in kwargs.items():
            formatted_prompt = formatted_prompt.replace(f"{{{key}}}", str(value))
        
        # Special handling for init template - now works with both template_name and template_content
        if template_name in ["init", "scaffold"] or "{sql_migrations}" in formatted_prompt:
            sql_migrations_template = self.load_prompt_template("sql_migrations")
            formatted_prompt = formatted_prompt.replace("{sql_migrations}", sql_migrations_template)
        
        return formatted_prompt
        
    def get_files_context(self, max_files: int = 60) -> str:
        """Get formatted context of existing files"""
        files_context = []
        
        # Get the most important files (limit by count to avoid token issues)
        important_extensions = ['.js', '.jsx', '.ts', '.tsx', '.json', '.css', '.scss', '.html', '.sql', '.py']
        important_files = []
        
        for file_path, content in self.memory.files.items():
            file_ext = os.path.splitext(file_path)[1]
            if file_ext in important_extensions:
                important_files.append((file_path, content))
                
        # Sort by importance and limit
        important_files = sorted(important_files, key=lambda x: os.path.splitext(x[0])[1] in ['.json', '.js', '.ts', '.jsx', '.tsx'])[:max_files]
        
        # Format files with code blocks
        for file_path, content in important_files:
            file_ext = os.path.splitext(file_path)[1][1:]  # Remove the dot
            files_context.append(f"### File: {file_path}\n```{file_ext}\n{content}\n```\n")
            
        if files_context:
            return "\n\n".join(files_context)
        else:
            return "No existing files available."
    
    def process_response(self, response: str) -> Dict[str, str]:
        """
        Process the generated files from the LLM response.
        Handles JSON parsing, extraction and file writing.
        """
        try:
            # Save the raw response
            # debug_file_path = os.path.join(self.project_dir, "debug_response.json")
            # with open(debug_file_path, "w", encoding="utf-8") as f:
            #     f.write(response)
            
            # Clean up the response
            response = response.strip()
            
            if response.startswith("```json"):
                response = response[7:]  # Remove ```json
            elif response.startswith("```"):
                response = response[3:]  # Remove ```
                
            if response.endswith("```"):
                response = response[:-3] 
            response = response.strip()
            
            # Try to repair malformed JSON if needed
            try:
                from json_repair import repair_json
                response = repair_json(response)
            except ImportError:
                logger.warning("json_repair package not available, skipping JSON repair")
            
            # Save preprocessed response
            # with open(os.path.join(self.project_dir, "preprocessed_response.json"), "w", encoding="utf-8") as f:
            #     f.write(response)
            
            # Parse JSON response
            try:
                files_data = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {str(e)}")
                
                # Try to extract JSON with regex as fallback
                try:
                    json_pattern = r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})'
                    matches = re.findall(json_pattern, response)
                    if matches:
                        extracted_json = matches[0]
                        files_data = json.loads(extracted_json)
                    else:
                        return {}
                except Exception as ex:
                    logger.error(f"Failed to extract JSON: {str(ex)}")
                    return {}
            
            # Process the files data
            generated_files = {}
            
            if isinstance(files_data, list):
                # Handle list of file objects
                for file_obj in files_data:
                    if isinstance(file_obj, dict) and 'path' in file_obj and 'content' in file_obj:
                        if isinstance(file_obj['content'], str):
                            self._write_file(file_obj['path'], file_obj['content'])
                            generated_files[file_obj['path']] = file_obj['content']
            
            elif isinstance(files_data, dict):
                # Check if we have a "files" and "migrations" structure
                if "files" in files_data and isinstance(files_data["files"], dict):
                    # Process regular files
                    for file_path, content in files_data["files"].items():
                        if isinstance(content, str):
                            self._write_file(file_path, content)
                            generated_files[file_path] = content
                    
                    # Process SQL migrations if present
                    if "migrations" in files_data and isinstance(files_data["migrations"], dict):
                        migrations_dir = os.path.join(self.project_dir, "migrations")
                        os.makedirs(migrations_dir, exist_ok=True)
                        
                        for file_name, content in files_data["migrations"].items():
                            if isinstance(content, str):
                                migration_path = os.path.join("migrations", file_name)
                                self._write_file(migration_path, content)
                                generated_files[migration_path] = content
                else:
                    # Process all files directly from dictionary
                    for file_path, content in files_data.items():
                        if isinstance(content, str):
                            self._write_file(file_path, content)
                            generated_files[file_path] = content
            
            # Update memory with the new files
            self.memory.add_files(generated_files)
            return generated_files
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def _write_file(self, file_path: str, content: str) -> bool:
        """Write a file to disk at the specified path"""
        try:
            # Verify content is a string
            if not isinstance(content, str):
                logger.error(f"Cannot write non-string content to {file_path}")
                return False
            
            # Create the full path
            full_path = os.path.join(self.project_dir, file_path)
            
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Validate JSON content before writing
            if file_path.endswith(('.json')):
                content = self._validate_json_content(file_path, content)
            
            # Write the file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Created file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False
    
    def _validate_json_content(self, filepath: str, content: str) -> str:
        """Validate and potentially fix JSON content"""
        if not filepath.endswith(('.json')):
            return content
            
        try:
            # Verify it's valid JSON
            json.loads(content)
            return content
        except json.JSONDecodeError:
            # Try to fix double-escaped JSON
            if '\\"' in content:
                fixed_content = content.replace('\\"', '"')
                try:
                    json.loads(fixed_content)
                    return fixed_content
                except json.JSONDecodeError:
                    pass
            
            return content 
    def get_tech_stack_name(self, tech_stack_number):
        """Convert tech stack number to full name"""
        tech_stacks = {
            "1": "Next.js (UI Only)",
            "2": "Next.js + Supabase"
        }
        return tech_stacks.get(tech_stack_number, "Unknown Tech Stack")
        
    def _get_reference_code_for_stack(self, tech_stack: str) -> str:
        """
        Get reference code based on the template stack.
        Note: We now use template stacks instead of tech stacks for reference code.
        """
        template_name = self.memory.context.get("template_name", "growith")
        
        return self._load_reference_project(template_name)
    
    def _load_reference_project(self, project_name: str) -> str:
        """
        Load reference code based on selected template stack.
        This method now loads from zip files in the templates/stacks directory.
        """

        # Special case for UI-only model (tech_stack="1")
        tech_stack = self.memory.context.get("tech_stack", "")
        if tech_stack == "1":
            return self._load_reference_zip("sample_ui_e-commerce")

        template_mapping = {
            "1": "e-commerce_template",       
            "2": "marketing_template",         
            "3": "crm",
            "4": "marketing_template",         
            "e-commerce_template": "e-commerce_template",
            "marketing_template": "marketing_template",
            "growith": "marketing_template",
            "crm": "crm",
         
        }
        
        zip_name = template_mapping.get(project_name, "e-commerce_template")
        return self._load_reference_zip(zip_name)
    
    def _load_reference_zip(self, zip_name: str) -> str:
        """Load reference code from a zip file using importlib.resources."""

        try:
            resource_path = f"templates/stacks/{zip_name}.zip"

            package = "gocodeo_cli"
            
         
            with resources.files(package).joinpath(resource_path).open('rb') as f:
                zip_data = io.BytesIO(f.read())
        except Exception as e:
            logger.error(f"Failed to load template zip file {zip_name}: {str(e)}")
            return ""

        relevant_extensions = [
            '.tsx', '.jsx', '.ts', '.js', '.json', '.css', '.scss',
            '.html', '.md', '.sql', '.py', '.config.js'
        ]

        exclude_dirs = ['node_modules', '.next', '.git', '__pycache__', 'dist', 'build', 'out']
        
        context_parts = []
        loaded_files_count = 0
        max_files = 80 
        
        try:
            with zipfile.ZipFile(zip_data) as zip_ref:
                file_list = zip_ref.namelist()
                
                for file_path in file_list:
                    if loaded_files_count >= max_files:
                        break
                    
                    if any(excluded in file_path for excluded in exclude_dirs):
                        continue
                    
                    file_ext = os.path.splitext(file_path)[1]
                    if file_ext not in relevant_extensions and not file_path.endswith('.config.js'):
                        continue
                    
                    try:
                        file_info = zip_ref.getinfo(file_path)
        
                        if file_info.file_size > 100 * 1024:
                            logger.info(f"Skipping large file: {file_path}")
                            continue
                        
                        content = zip_ref.read(file_path).decode('utf-8')
                        context_parts.append(f"### Reference File: {file_path}\n```\n{content}\n```\n")
                        loaded_files_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error reading file {file_path} from zip: {str(e)}")
                        continue
        
        except Exception as e:
            logger.error(f"Error processing zip file: {str(e)}")
            return ""
        finally:
            zip_data.close()
        
        logger.info(f"Loaded {loaded_files_count} files from {zip_name}")
        return "\n\n".join(context_parts)