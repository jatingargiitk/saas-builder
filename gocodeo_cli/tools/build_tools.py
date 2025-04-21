import os
from typing import Dict, Any
from pathlib import Path

from ..agents.base import BaseTool, BaseAgent
from ..services.llm_service import llm
from ..services.project_state import ProjectStage

class InitializeTool(BaseTool):
    """Tool for initializing a new project."""
    
    def __init__(self):
        super().__init__(
            name="initialize",
            description="Initialize project scaffold with basic structure"
        )
    
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
        # try:
        #     domain_analysis = await llm.analyze_project(description, model)
        #     # Load the init template
        #     init_template = agent.load_prompt_template("init")
        #     # Load and format the init prompt
        # except Exception as e:
        #     print(e,"error in domain_analysis")
        init_prompt = agent.format_prompt(
            "init", 
            project_name=name,
            project_description=description,
            tech_stack=agent.get_tech_stack_name(tech_stack)
        )
        
        # Load system prompt
        system_prompt = agent.load_prompt_template("system")
        
        # Generate scaffold code - we don't print here since the command already prints the message
        # agent.console.print("🔄 Initializing project...")
        
        try:
            response = llm.generate_code(
                prompt=init_prompt,
                model=model,  # Use the exact model passed in, don't override
                system_prompt=system_prompt
            )
            
            # Process response and write files
            files = agent.process_response(response)
            
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
            agent.memory.add_message("system", f"Project initialization failed: {str(e)}")
            return f"❌ Project initialization failed: {str(e)}"

class AddAuthTool(BaseTool):
    """Tool for adding authentication to a project."""
    
    def __init__(self):
        super().__init__(
            name="add_auth",
            description="Add authentication system to the project"
        )
    
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
        
        # Extract project details
        model = agent.memory.context.get("model", kwargs.get("model", "claude-3-sonnet"))
        
        # Get existing files context
        existing_files = agent.get_files_context()
        
        # Load and format the auth prompt
        auth_prompt = agent.format_prompt(
            "auth",
            project_name=agent.memory.context.get("project_name", ""),
            project_description=agent.memory.context.get("project_description", ""),
            tech_stack=agent.memory.context.get("tech_stack", "1"),
            existing_files=existing_files
        )
        
        # Load system prompt
        system_prompt = agent.load_prompt_template("system")
        
        # Generate auth code - don't print here since the build_agent already prints this
        # agent.console.print("🔒 Adding authentication...")
        
        try:
           
            response = llm.generate_code(
                prompt=auth_prompt,
                model=model,
                system_prompt=system_prompt
            )
            
            # Process response and write files
            files = agent.process_response(response)
            
            if not files:
                agent.memory.add_message("system", "Authentication implementation failed: No files generated")
                return "❌ Authentication implementation failed"
            
            # Update agent state
            agent.memory.add_message("system", f"Authentication added with {len(files)} files")
            
            return "✓  Task2 completed:  Authentication added successfully"
            
        except Exception as e:
            agent.memory.add_message("system", f"Authentication implementation failed: {str(e)}")
            return f"❌ Authentication implementation failed: {str(e)}"

class AddDataTool(BaseTool):
    """Tool for adding data persistence to a project."""
    
    def __init__(self):
        super().__init__(
            name="add_data",
            description="Add data persistence layer to the project"
        )
    
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
        
        # Get existing files context
        existing_files = agent.get_files_context()
        
        # Load and format the data prompt
        data_prompt = agent.format_prompt(
            "data",
            project_name=agent.memory.context.get("project_name", ""),
            project_description=agent.memory.context.get("project_description", ""),
            tech_stack=agent.memory.context.get("tech_stack", "1"),
            existing_files=existing_files
        )
        
        # Load system prompt
        system_prompt = agent.load_prompt_template("system")
        
        # Generate data persistence code - don't print here since the build_agent already prints this
        # agent.console.print("💾 Adding data persistence...")
        
        try:
            response = llm.generate_code(
                prompt=data_prompt,
                model=model,
                system_prompt=system_prompt
            )
            
            # Process response and write files
            files = agent.process_response(response)
            
            if not files:
                agent.memory.add_message("system", "Data persistence implementation failed: No files generated")
                return "❌ Data persistence implementation failed"
            
            # Update agent state
            agent.memory.add_message("system", f"Data persistence added with {len(files)} files")
            
            return "✓  Task3 completed: Supabase integration and data persistence configured successfully"
            
        except Exception as e:
            agent.memory.add_message("system", f"Data persistence implementation failed: {str(e)}")
            return f"❌ Data persistence implementation failed: {str(e)}" 