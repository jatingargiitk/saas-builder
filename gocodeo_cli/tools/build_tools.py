import os
from typing import Dict, Any
from pathlib import Path

from ..agents.base import BaseTool, BaseAgent
from ..services.llm_service import llm
from ..services.project_state import ProjectStage
from rich.console import Console
from ..utils.progress import ProgressSpinner

class InitializeTool(BaseTool):
    """Tool for initializing a new project."""
    
    def __init__(self):
        super().__init__(
            name="initialize",
            description="Initialize project scaffold with basic structure"
        )
        self.console = Console()
    
    async def execute(self, agent: BaseAgent, **kwargs) -> str:
        """
        Initialize the project with scaffold files.
        
        Args:
            agent: The agent executing this tool
            kwargs: Additional arguments including project details
        
        Returns:
            Result message
        """
        # Update agent state
        agent.state = "INITIALIZING"
        agent.memory.add_message("system", "Starting project initialization")
        
        # Extract project details
        name = kwargs.get("name", "unnamed-project")
        description = kwargs.get("description", "No description provided")
        tech_stack = kwargs.get("tech_stack", "1")  # Default to Next.js + Supabase
        model = kwargs.get("model", "claude-3-sonnet")
        template_name = kwargs.get("template_name", "growith")  # Default to SaaS Marketing template
        prompt_template = kwargs.get("prompt_template", "init_ui.txt" if tech_stack == "1" else "init.txt")
        prompt_content = agent.load_prompt_template(prompt_template.replace(".txt", ""))
        # extra_prompt = ""
        # if template_name == "crm" and tech_stack == "2":
        #     extra_prompt = "\n ## ULTRA IMPORTANT: Verify that all files present in the 'ui' directory (like toast-related files and other shared components used elsewhere) exist, are correctly named, syntactically valid, and fully implemented if used in the code."
        # prompt_content += extra_prompt
        # Store tech_stack in memory context before loading reference code
        agent.memory.update_context("tech_stack", tech_stack)
        
        # Create and start progress spinner
        spinner = ProgressSpinner("🔨 Task1: Running UI Agent", self.console)
        spinner.start()
        
        try:
            # Get reference code from the template stack - pass both template_name and tech_stack
            reference_code_context = agent._load_reference_project(template_name)
            
            init_prompt = agent.format_prompt(
                template_content=prompt_content,
                project_name=name,
                project_description=description,
                tech_stack=agent.get_tech_stack_name(tech_stack),
                reference_code=reference_code_context  
            )
            
            # Load system prompt
            system_prompt = agent.load_prompt_template("system")
            
            response = llm.generate_code(
                prompt=init_prompt,
                model=model,  # Use the exact model passed in, don't override
                system_prompt=system_prompt
            )
            
            # Process response and write files
            files = agent.process_response(response)
            
            # Stop the spinner before returning result
            spinner.stop(preserve_message=True)
            
            if not files:
                agent.memory.add_message("system", "Project initialization failed: No files generated")
                return "❌ Project initialization failed"
            
            # Update agent state
            agent.memory.add_message("system", f"Project initialized with {len(files)} files")
            agent.memory.update_context("project_name", name)
            agent.memory.update_context("project_description", description)
            agent.memory.update_context("tech_stack", tech_stack)
            agent.memory.update_context("model", model)
            
            return "✓  Task1 completed:  UI generated successfully"
            
        except Exception as e:
            # Make sure to stop spinner on error
            spinner.stop(preserve_message=True)
            agent.memory.add_message("system", f"Project initialization failed: {str(e)}")
            return f"❌ Project initialization failed: {str(e)}"

class AddAuthTool(BaseTool):
    """Tool for adding authentication to a project."""
    
    def __init__(self):
        super().__init__(
            name="add_auth",
            description="Add authentication system to the project"
        )
        self.console = Console()
    
    async def execute(self, agent: BaseAgent, **kwargs) -> str:
        """
        Add authentication system to the project.
        
        Args:
            agent: The agent executing this tool
            kwargs: Additional arguments
        
        Returns:
            Result message
        """
        # Update agent state
        agent.state = "ADDING_AUTH"
        agent.memory.add_message("system", "Starting authentication implementation")
        tech_stack = kwargs.get("tech_stack", "1")
        template_name = kwargs.get("template_name", "1")
        # Extract project details
        model = agent.memory.context.get("model", kwargs.get("model", "claude-3-sonnet"))
        self.console.print("\n")
        # Create and start progress spinner
        spinner = ProgressSpinner("🔒 Task2: Running Auth Agent", self.console)
        spinner.start()
        
        try:
            # Load the auth prompt template
            prompt_content = agent.load_prompt_template("auth")
            extra_prompt = ""
            if template_name == "crm" and tech_stack == "2":
                extra_prompt = "\n ## ULTRA IMPORTANT: Verify that all files present in the 'ui' directory (like toast-related files and other shared components used elsewhere) exist, are correctly named, syntactically valid, and fully implemented if used in the code."
            prompt_content += extra_prompt

            # Get existing files context
            existing_files = agent.get_files_context()
            
            # Get reference code from the template stack
            reference_code_context = agent._get_reference_code_for_stack("")
            
            # Load and format the auth prompt
            auth_prompt = agent.format_prompt(
                template_content=prompt_content,
                project_name=agent.memory.context.get("project_name", ""),
                project_description=agent.memory.context.get("project_description", ""),
                tech_stack=agent.memory.context.get("tech_stack", "1"),
                existing_files=existing_files,
                reference_code=reference_code_context
            )
            
            # Load system prompt
            system_prompt = agent.load_prompt_template("system")
            
            response = llm.generate_code(
                prompt=auth_prompt,
                model=model,
                system_prompt=system_prompt
            )
            
            # Process response and write files
            files = agent.process_response(response)
            
            # Stop the spinner before returning result
            spinner.stop(preserve_message=True)
            
            if not files:
                agent.memory.add_message("system", "Authentication implementation failed: No files generated")
                return "❌ Authentication implementation failed"
            
            # Update agent state
            agent.memory.add_message("system", f"Authentication added with {len(files)} files")
            
            return "✓  Task2 completed:  Authentication added successfully"
            
        except Exception as e:
            # Make sure to stop spinner on error
            spinner.stop(preserve_message=True)
            agent.memory.add_message("system", f"Authentication implementation failed: {str(e)}")
            return f"❌ Authentication implementation failed: {str(e)}"

class AddDataTool(BaseTool):
    """Tool for adding data persistence to a project."""
    
    def __init__(self):
        super().__init__(
            name="add_data",
            description="Add data persistence layer to the project"
        )
        self.console = Console()
    
    async def execute(self, agent: BaseAgent, **kwargs) -> str:
        """
        Add data persistence layer to the project.
        
        Args:
            agent: The agent executing this tool
            kwargs: Additional arguments
        
        Returns:
            Result message
        """
        # Update agent state
        agent.state = "ADDING_DATA"
        agent.memory.add_message("system", "Starting data persistence implementation")
        
        # Extract project details
        model = agent.memory.context.get("model", kwargs.get("model", "claude-3-sonnet"))
        self.console.print("\n")

        # Create and start progress spinner
        spinner = ProgressSpinner("💾 Task3: Running Supabase Agent", self.console)
        spinner.start()
        
        try:
            # Load the data prompt template
            prompt_content = agent.load_prompt_template("data")
            tech_stack = kwargs.get("tech_stack", "1")
            template_name = kwargs.get("template_name", "1")
            extra_prompt = ""
            if template_name == "crm" and tech_stack == "2":
                extra_prompt = "\n ## ULTRA IMPORTANT: Verify that all files must be Created & present , mainly in the 'ui' directory (like toast-related files and other shared components used elsewhere) exist, are correctly named, syntactically valid, and fully implemented if used in the code."
            prompt_content += extra_prompt
            # Get existing files context
            existing_files = agent.get_files_context()
            
            # Get reference code from the template stack
            reference_code_context = agent._get_reference_code_for_stack("")
            
            # Load and format the data prompt
            data_prompt = agent.format_prompt(
                template_content=prompt_content,
                project_name=agent.memory.context.get("project_name", ""),
                project_description=agent.memory.context.get("project_description", ""),
                tech_stack=agent.memory.context.get("tech_stack", "1"),
                existing_files=existing_files,
                reference_code=reference_code_context
            )
            
            # Load system prompt
            system_prompt = agent.load_prompt_template("system")
            
            response = llm.generate_code(
                prompt=data_prompt,
                model=model,
                system_prompt=system_prompt
            )
            
            # Process response and write files
            files = agent.process_response(response)
            
            # Stop the spinner before returning result
            spinner.stop(preserve_message=True)
            
            if not files:
                agent.memory.add_message("system", "Data persistence implementation failed: No files generated")
                return "❌ Data persistence implementation failed"
            
            # Update agent state
            agent.memory.add_message("system", f"Data persistence added with {len(files)} files")
            
            return "✓  Task3 completed: Supabase integration and data persistence configured successfully"
            
        except Exception as e:
            # Make sure to stop spinner on error
            spinner.stop(preserve_message=True)
            agent.memory.add_message("system", f"Data persistence implementation failed: {str(e)}")
            return f"❌ Data persistence implementation failed: {str(e)}"

    def _get_tech_stack_name(self, tech_stack: str) -> str:
        """Get the full name of a tech stack from its code."""
        tech_stacks = {
            "1": "Next.js (UI Only)",
            "2": "Next.js + Supabase",
            "3": "Next.js with MongoDB"
        }
        return tech_stacks.get(tech_stack, "Unknown Tech Stack") 
    