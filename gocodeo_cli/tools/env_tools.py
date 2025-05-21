import os
from typing import Dict, Any
from pathlib import Path

from ..agents.base import BaseTool, BaseAgent

class EnvFileCreatorTool(BaseTool):
    """Tool for creating environment configuration files."""
    
    def __init__(self):
        super().__init__(
            name="create_env",
            description="Create .env file with configuration for the project"
        )
    
    async def execute(self, agent: BaseAgent, **kwargs) -> str:
        """
        Create .env file with provided configuration.
        
        Args:
            agent: The agent executing this tool
            kwargs: Additional arguments including project configuration
            
        Returns:
            Result message
        """
        try:
            # Extract parameters
            tech_stack = kwargs.get("tech_stack", agent.memory.context.get("tech_stack", "1"))
            
            # Generate content based on tech stack
            content = self._get_env_content(tech_stack, agent.memory.context)
            
            # Create .env file in project directory
            env_path = os.path.join(agent.project_dir, ".env.local")
            
            # Write content to file
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
            
             # Log success but don't display to console
            agent.memory.add_message("system", f"Created environment file at {env_path}")
            return f""
            
        except Exception as e:
            agent.memory.add_message("system", f"Failed to create environment file: {str(e)}")
            return f"❌ Failed to create environment file: {str(e)}"
    
    def _get_env_content(self, tech_stack: str, context: Dict[str, Any] = None) -> str:
        """Generate environment content based on tech stack."""
        if tech_stack == "1" or tech_stack == "2" or self._get_tech_stack_name(tech_stack) == "Next.js + Supabase":

            # Use provided credentials if available, otherwise use defaults
            supabase_url = context.get("supabase_url", "") if context else ""
            supabase_anon_key = context.get("supabase_anon_key", "") if context else ""
            supabase_token = context.get("supabase_token", "") if context else ""
            
            return (
                f"NEXT_PUBLIC_SUPABASE_URL={supabase_url}\n"
                f"NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_anon_key}\n"
                f"SUPABASE_ACCESS_TOKEN={supabase_token}"
            )
        
        else:  # MongoDB or other stacks
            return (
                "MONGODB_URI=YOUR_MONGODB_URI\n"
                "NEXTAUTH_SECRET=YOUR_NEXTAUTH_SECRET\n"
                "NEXTAUTH_URL=http://localhost:3000\n"
            )
    
    def _get_tech_stack_name(self, tech_stack: str) -> str:
        """Get the full name of a tech stack from its code."""
        tech_stacks = {
            "1": "Next.js (UI Only)",
            "2": "Next.js + Supabase",
            "3": "Next.js with MongoDB"
        }
        return tech_stacks.get(tech_stack, "Unknown Tech Stack") 