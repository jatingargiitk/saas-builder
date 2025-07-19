"""
Service for interacting with LLM APIs.
"""
import json
import os
from typing import Optional

import anthropic
import google.generativeai as genai
import openai
from anthropic import AnthropicVertex
from openai import OpenAI
from rich import print
from rich.console import Console
from gocodeo_cli.utils import config
import tiktoken
# Initialize console
console = Console()


class LLMService:
    """Service for generating code using various LLM providers."""
    
    
    def __init__(self):
        """Initialize LLM clients."""
        self.openai = None
        self.anthropic = None
        self.gemini_available = False
        
        # We'll initialize clients on-demand when needed
    def _ensure_openai_client(self):
        """Ensure OpenAI client is initialized, prompt for key if needed."""
        if self.openai is not None:
            return
        
        openai_key = config.get_openai_api_key()
        if not openai_key:
            openai_key = config.prompt_for_api_key("gpt")
            config.set_openai_api_key(openai_key)
            
        self.openai = OpenAI(api_key=openai_key)
    
    def _ensure_anthropic_client(self):
        """Ensure Anthropic client is initialized, prompt for key if needed."""
        if self.anthropic is not None:
            return
        
        anthropic_key = config.get_anthropic_api_key()
        if not anthropic_key:
            anthropic_key = config.prompt_for_api_key("claude")
            config.set_anthropic_api_key(anthropic_key)
            
        self.anthropic = anthropic.Anthropic(api_key=anthropic_key)
    
    def _ensure_gemini_available(self):
        """Ensure Gemini is available, prompt for key if needed."""
        if self.gemini_available:
            return
        
        gemini_key = config.get_google_api_key()
        if not gemini_key:
            gemini_key = config.prompt_for_api_key("gemini")
            config.set_google_api_key(gemini_key)
            
        try:
            # Configure Gemini with API key
            genai.configure(api_key=gemini_key)
            self.gemini_available = True
        except Exception as e:
            console.print(f"[red]Error configuring Gemini: {str(e)}[/red]")
            self.gemini_available = False

    def generate_code(
        self,
        prompt: str,
        model: str = "claude-3-7-sonnet",
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate code using the specified LLM.
        
        Args:
            prompt: The user prompt
            model: Model to use (default: claude-3.7-sonnet)
            system_prompt: Optional system prompt
            
        Returns:
            Generated code as string
        """
        import time
        start_time = time.time()
        
        try:
            # Route to appropriate provider
            if model.startswith("gpt"):
                self._ensure_openai_client()
                response = self._generate_with_openai(prompt, model, system_prompt)
            elif model.startswith("claude"):
                self._ensure_anthropic_client()
                response = self._generate_with_anthropic(prompt, model, system_prompt)
            elif model.startswith("gemini"):
                self._ensure_gemini_available()
                if not self.gemini_available:
                    raise ValueError("Failed to configure Google API. Please check your API key.")
                response = self._generate_with_gemini(prompt, model, system_prompt)
            else:
                raise ValueError(f"Unsupported model: {model}")
            
            
            return response
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"\n[red]Code generation failed after {elapsed_time:.2f} seconds[/red]")
            print(f"[red]Error: {str(e)}[/red]")
            raise
    
    def _generate_with_openai(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate code using OpenAI models."""
        if self.openai is None:
            raise ValueError("OpenAI client not initialized")
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        
        
        response = self.openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=32000,
        )
        return response.choices[0].message.content
    
    def _generate_with_anthropic(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate code using Anthropic models."""
        if self.anthropic is None:
            raise ValueError("Anthropic client not initialized")
            
        # Combine system prompt and user prompt
        messages = []
        if system_prompt:
            messages.append({
                "role": "assistant",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        model="claude-sonnet-4-20250514"
        response = self.anthropic.messages.create(
            model=model,
            messages=messages,
            temperature=0,
            max_tokens=50000,
        )
        
        return response.content[0].text
    
    def _generate_with_gemini(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate code using Google's Gemini models."""
        if not self.gemini_available:
            raise ValueError("Gemini not configured properly")
        
        try:
            # Configure model (normalize model name)
            if ":" in model:
                model_name = model
            else:
                model_name = model
         
            # Create model instance
            gemini_model = genai.GenerativeModel(model_name)
           
            # Set generation config to ensure we get complete responses
            generation_config = {
                "temperature": 0.2,  
                "max_output_tokens": 50000,
            }
            
            # Combine prompts - for code generation, we need to explicitly tell Gemini to generate JSON
            if system_prompt:
                # For code generation, parse the system prompt to find the JSON format instructions
                json_format_note = ""
                if "CRITICAL JSON FILE FORMATTING (HIGHEST PRIORITY):" in system_prompt:
                    json_format_note = """\n\n  IMPORTANT: Format your response as a valid JSON object where:
                                        1. All file paths are keys
                                        2. File contents are string values
                                        3. Use proper JSON string escaping
                                        4. Do not add line breaks within the JSON structure itself
                                        5. Use only ASCII characters in your response. Do not use any special characters, emojis, or non-ASCII symbols."
                                        6. ULTRA IMPORTANT:AVOID ERRORS LIKE THIS: Error: 'charmap' codec can't encode characters in position 1096-1098: character maps to<undefined>
                                       7. Escape newlines in file contents with \\n
                                        Example format:
                                        {
                                        "file.txt": "line1\\nline2\\nline3"
                                        }"""
                    
                
                full_prompt = f"{system_prompt}{json_format_note}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            # Generate response with safety settings to avoid content filtering
            safety_settings = {
                "HARASSMENT": "block_none",
                "HATE": "block_none",
                "SEXUAL": "block_none",
                "DANGEROUS": "block_none",
            }
            
            # Generate response
            response = gemini_model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
               
            )
           
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 4:
                        print("\nWarning: Response was blocked due to potential copyright recitation")
                        raise ValueError("Response contained copyrighted material. Please modify your prompt to avoid requesting copyrighted content.")
            elif not hasattr(response, 'text') or not response.text:
                print("\nWarning: Empty response received from Gemini")
                raise ValueError("Received empty response from Gemini API. This might be due to safety filtering or other content restrictions.")

            # Parse JSON from the response if needed
            if "CRITICAL: Your response MUST be a valid JSON object" in system_prompt:
                try:
                    # Attempt to extract JSON from a potentially messy response
                    # First, find something that looks like the start of a JSON object
                    text = response.text
                    start_idx = text.find('{')
                    if start_idx >= 0:
                        # Find the matching end bracket
                        open_braces = 0
                        for i in range(start_idx, len(text)):
                            if text[i] == '{':
                                open_braces += 1
                            elif text[i] == '}':
                                open_braces -= 1
                                if open_braces == 0:
                                    # Found a complete JSON object
                                    extracted_json = text[start_idx:i+1]
                                    try:
                                        # Validate it's proper JSON
                                        json.loads(extracted_json)
                                        # print("Found and validated JSON object in response")
                                        return extracted_json
                                    except:
                                        # Not valid JSON, continue searching
                                        pass
                
                    # If we got here, we couldn't extract a valid JSON object
                except Exception as e:
                    print(f"Error parsing JSON from Gemini response: {str(e)}")
            
            # Return the text as-is
            return response.text
            
            
        except Exception as e:
            print(f"Error with Gemini model: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to generate response with Gemini: {str(e)}")

# Create a singleton instance
llm = LLMService() 