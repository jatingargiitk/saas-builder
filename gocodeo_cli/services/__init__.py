"""
Service layer for the GoCodeo CLI.
"""
from gocodeo_cli.services.llm_service import LLMService

# Create singleton instances
llm = LLMService()
