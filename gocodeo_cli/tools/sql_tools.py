import os
import re
import json
import subprocess
from typing import Dict, Any, List, Optional
import requests
from rich.console import Console

from ..agents.base import BaseTool, BaseAgent
from ..services.llm_service import llm

class SqlMigrationTool(BaseTool):
    """Tool for running SQL migrations."""
    
    def __init__(self):
        super().__init__(
            name="run_migrations",
            description="Run SQL migrations from the migrations directory"
        )
        self.retry_count = 0
        self.max_retries = 2
        self.console = Console()
    
    async def execute(self, agent: BaseAgent, **kwargs) -> str:
        """
        Execute SQL migrations from the migrations directory.
        
        Args:
            agent: The agent executing this tool
            kwargs: Additional arguments
            
        Returns:
            Result message
        """
        try:
            # Get project directory
            project_dir = agent.project_dir
            migrations_dir = os.path.join(project_dir, "migrations")
            
            # Check if migrations directory exists
            if not os.path.exists(migrations_dir):
                agent.memory.add_message("system", "No migrations directory found")
                return "❓ No migrations directory found, skipping SQL execution."
            
            # Find SQL migration files
            sql_files = [f for f in os.listdir(migrations_dir) if f.endswith('.sql')]
            sql_files.sort()  # Sort to ensure correct execution order
            
            if not sql_files:
                agent.memory.add_message("system", "No SQL migration files found")
                return "❓ No SQL migration files found, skipping SQL execution."
            
            # Log start of migrations
            agent.memory.add_message("system", f"Found {len(sql_files)} SQL migration files")
            self.console.print(f"\n🛢️  Task4: Running Supabase Agent")
            
            # Get env file values for Supabase connection
            supabase_url, supabase_key, supabase_token = self._get_supabase_credentials(project_dir, agent.memory.context)
            if not supabase_url or not supabase_key:
                agent.memory.add_message("system", "No Supabase credentials found, will simulate execution")
                self.console.print("[yellow]⚠️ No Supabase credentials found, simulating execution[/yellow]")
                return "⚠️ No Supabase credentials found, simulating execution."
                
            # Extract project ID from supabase URL
            project_id = self._extract_project_id(supabase_url)
            if not project_id:
                agent.memory.add_message("system", "Failed to extract project ID from Supabase URL")
                self.console.print("[yellow]⚠️ Failed to extract project ID from Supabase URL[/yellow]")
                return "⚠️ Failed to extract project ID from Supabase URL."
                
            # Process each migration file
            results = []
            successful_count = 0
            
            for file_name in sql_files:
                file_path = os.path.join(migrations_dir, file_name)
                
                # Read SQL from file
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Execute SQL
                self.console.print(f"  ↳ Running {file_name}")
                
                try:
                    # Execute the SQL via Supabase API
                    execution_result = self.execute_supabase_sql(
                        sql_commands=sql_content,
                        supabase_project_id=project_id,
                        supabase_token=supabase_token
                    )
                    
                    if "error" in execution_result:
                        error_message = execution_result["error"]
                        self.console.print(f"[red]❌ Error in {file_name}: {error_message}[/red]")
                        
                        # Try to fix SQL
                        success, fixed_sql = await self.handle_sql_error(
                            sql_content=sql_content,
                            error_message=error_message,
                            file_path=file_path,
                            file_name=file_name,
                            agent=agent,
                            project_id=project_id,
                            supabase_key=supabase_token
                        )
                        
                        if success:
                            successful_count += 1
                            results.append(f"✓ Successfully executed {file_name} (after fixing)")
                        else:
                            results.append(f"❌ Failed to execute {file_name}: {error_message}")
                    else:
                        # Success case
                        # self.console.print(f"[green]✓ Executed {file_name} successfully[/green]")
                        successful_count += 1
                        results.append(f"✓ Successfully executed {file_name}")
                
                except Exception as e:
                    error_msg = str(e)
                    self.console.print(f"[red]❌ Error executing {file_name}: {error_msg}[/red]")
                    results.append(f"❌ Failed to execute {file_name}: {error_msg}")
            
            # Reset retry counter
            self.retry_count = 0
            
            
            # Return summary
            return f"✓ Task4 completed: Executed {successful_count} of {len(sql_files)} migrations successfully"
            
        except Exception as e:
            agent.memory.add_message("system", f"Failed to execute SQL migrations: {str(e)}")
            return f"❌ Failed to execute SQL migrations: {str(e)}"
    
    async def handle_sql_error(
        self, 
        sql_content: str, 
        error_message: str, 
        file_path: str,
        file_name: str,
        agent: BaseAgent,
        project_id: str,
        supabase_key: str
    ) -> tuple[bool, str]:
        """
        Handle SQL errors by using LLM to fix them and updating the file.
        
        Args:
            sql_content: Original SQL content that failed
            error_message: Error message from Supabase
            file_path: Path to the SQL file
            file_name: Name of the SQL file
            agent: The agent executing this tool
            project_id: Supabase project ID
            supabase_key: Supabase API key
            
        Returns:
            Tuple of (success_flag, fixed_sql_content)
        """
        for attempt in range(1, self.max_retries + 1):
            self.console.print(f"[yellow]⚠️ Running Debugger agent (attempt {attempt}/{self.max_retries})[/yellow]")
            
            # Get the selected model from agent context
            model = agent.memory.context.get("model", "claude-3.5-sonnet")
            
            # Create prompt for fixing the SQL
            prompt = (
                f"You are an expert SQL developer specializing in PostgreSQL and Supabase.\n\n"
                f"I tried to execute the following SQL command and got an error:\n\n"
                f"```sql\n{sql_content}\n```\n\n"
                f"Error message: {error_message}\n\n"
                f"Please provide a fixed version of this SQL command that will work correctly. "
                f"If the error indicates an object already exists (like 'trigger already exists', 'relation already exists', etc.), "
                f"remove the statements that try to create those existing objects entirely. "
                f"For example, if there's an error like 'trigger X already exists', remove the entire CREATE TRIGGER statement for X. "
                f"Return ONLY the fixed SQL without any explanations, comments, or markdown formatting. "
                f"The response should be the complete corrected SQL that can be executed directly."
            )
            
            try:
                
                # Call LLM to fix SQL
                system_prompt = "You are an expert SQL fixer. Return only the fixed SQL without any explanations or markdown."
                fixed_sql =  llm.generate_code(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt
                )
                # print(f"Fixed SQL: {fixed_sql}")
                # Clean up any markdown formatting that might be in the response
                fixed_sql = self._clean_sql_response(fixed_sql)
                
                # Try to execute the fixed SQL
                self.console.print(f"[blue]🔄 Trying fixed SQL...[/blue]")
                execution_result = self.execute_supabase_sql(
                    sql_commands=fixed_sql,
                    supabase_project_id=project_id,
                    supabase_token=supabase_key
                )
                
                if "error" not in execution_result:
                    # Success! Update the original file with the fixed SQL
                    self.console.print(f"[green]✓ SQL fix successful![/green]")
                    
                    # Save the fixed SQL to the original file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_sql)
                    
                    self.console.print(f"[green]✓ Updated {file_name} with fixed SQL[/green]")
                    return True, fixed_sql
                else:
                    # Still failing, try again with the new error message
                    error_message = execution_result["error"]
                    self.console.print(f"[red]❌ Fixed SQL still has error: {error_message}[/red]")
            
            except Exception as e:
                self.console.print(f"[red]❌ Error while fixing SQL: {str(e)}[/red]")
        
        # If we get here, all attempts failed
        self.console.print(f"[red]❌ Failed to fix SQL after {self.max_retries} attempts[/red]")
        return False, sql_content
    
    def _clean_sql_response(self, sql_response: str) -> str:
        """Clean up SQL response from LLM to ensure it's executable."""
        # Remove any markdown code blocks
        sql = re.sub(r'```sql\n', '', sql_response)
        sql = re.sub(r'```', '', sql)
        
        # Remove any prefixed comments that might be explaining the fix
        lines = sql.splitlines()
        clean_lines = []
        
        # Skip any explanatory text at the beginning
        content_started = False
        for line in lines:
            # Skip initial empty lines
            if not content_started and not line.strip():
                continue
                
            # Consider content has started once we hit a non-empty line
            content_started = True
            
            # If the line starts with -- or # and is likely an explanation, skip it
            if not content_started and (line.strip().startswith('--') or line.strip().startswith('#')):
                if "fix" in line.lower() or "correct" in line.lower() or "updated" in line.lower():
                    continue
            
            clean_lines.append(line)
        
        return '\n'.join(clean_lines).strip()
    
    def execute_supabase_sql(self, sql_commands, supabase_project_id, supabase_token):
        """
        Execute SQL commands on Supabase using the REST API.
        
        Args:
            sql_commands: SQL commands to execute
            supabase_project_id: Supabase project ID
            supabase_token: Supabase token (anon key)
            
        Returns:
            Dict with results or error
        """
        url = f"https://api.supabase.com/v1/projects/{supabase_project_id}/database/query"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {supabase_token}"
        }

        payload = {
            "query": sql_commands
        }
        payload_json = json.dumps(payload)
        try:
            response = requests.post(url, headers=headers, data=payload_json)
            response.raise_for_status()
            sql_result = response.json()
            return sql_result

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def _extract_project_id(self, supabase_url: str) -> str:
        """Extract project ID from Supabase URL."""
        # Extract the project ID from URL like https://ijdgpxhosdgcwbmvqmps.supabase.co
        match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
        if match:
            return match.group(1)
        return ""
    
    def _get_supabase_credentials(self, project_dir: str, memory_context: Dict[str, Any] = None) -> tuple:
        """Extract Supabase credentials from .env file."""
        # First check memory context if available
        if memory_context:
            context_url = memory_context.get("supabase_url")
            context_key = memory_context.get("supabase_anon_key")
            context_token = memory_context.get("supabase_token")
            
            if context_url and context_key and context_token:
                return context_url, context_key, context_token
        
        # Otherwise check the .env files
        env_paths = [
            os.path.join(project_dir, ".env"),
            os.path.join(project_dir, ".env.local"),
            os.path.join(project_dir, ".env.development"),
        ]
        
        supabase_url = None
        supabase_key = None
        supabase_token = None
        
        for path in env_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    env_content = f.read()
                    
                    # Extract Supabase URL
                    url_match = re.search(r'NEXT_PUBLIC_SUPABASE_URL=([^\n]+)', env_content)
                    if url_match:
                        supabase_url = url_match.group(1).strip()
                    
                    # Extract Supabase key
                    key_match = re.search(r'NEXT_PUBLIC_SUPABASE_ANON_KEY=([^\n]+)', env_content)
                    if key_match:
                        supabase_key = key_match.group(1).strip()
                    
                    # Extract Supabase token
                    token_match = re.search(r'SUPABASE_ACCESS_TOKEN=([^\n]+)', env_content)
                    if token_match:
                        supabase_token = token_match.group(1).strip()
                    
                    if supabase_url and supabase_key and supabase_token:
                        break
        

            
        return supabase_url, supabase_key, supabase_token 