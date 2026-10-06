"""
LLM Service Module

Handles communication with Groq for generating repository explanations.
"""

import os
from typing import Dict, Optional, List
import httpx
from dotenv import load_dotenv

load_dotenv()

# Groq configuration. The API key must come from the environment or the
# hosting provider's secret store; never commit it to the repository.
GROQ_API_URL = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
MAX_CONTEXT_CHARS = 60000


class LLMService:
    """
    Service for generating explanations using Groq.
    """

    def __init__(self, host: str = None, model: str = None, api_key: str = None):
        """
        Initialize the LLM service.

        Args:
            host: Groq API base URL.
            model: Model name to use.
            api_key: Groq API key.
        """
        self.host = (host or GROQ_API_URL).rstrip('/')
        self.model = model or GROQ_MODEL
        self.api_key = api_key or GROQ_API_KEY
        self._has_api_key = bool(
            self.api_key and not self.api_key.startswith('replace_with_')
        )

    def generate_explanation(
        self,
        files_context: List[Dict[str, str]],
        max_tokens: int = 4096
    ) -> Optional[str]:
        """
        Generate an explanation for the repository.

        Args:
            files_context: List of file contexts with path and content.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated explanation or None if generation failed.
        """
        try:
            # Build the prompt with all file contents
            prompt = self._build_prompt(files_context)

            if not self._has_api_key:
                print('Groq API key is not configured.')
                return None

            response = httpx.post(
                f'{self.host}/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You explain software repositories clearly and accurately for students.'
                        },
                        {'role': 'user', 'content': prompt},
                    ],
                    'temperature': 0.7,
                    'max_completion_tokens': min(max_tokens, 4096),
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content'].strip()

        except Exception as e:
            print(f"Error generating explanation with Groq: {e}")
            return None

    def _build_prompt(self, files_context: List[Dict[str, str]]) -> str:
        """
        Build the prompt for the LLM.

        Args:
            files_context: List of file contexts.

        Returns:
            Formatted prompt string.
        """
        # Keep the complete prompt bounded even when the caller provides many
        # files. Files are already sorted by relevance by the processor.
        top_files = []
        used_chars = 0
        for file_info in files_context:
            remaining = MAX_CONTEXT_CHARS - used_chars
            if remaining <= 0:
                break
            content = file_info['content']
            if len(content) > remaining:
                content = content[:remaining] + "\n\n... (context truncated)"
            top_files.append({**file_info, 'content': content})
            used_chars += len(content)

        # Build file content section
        file_contents = []
        for file_info in top_files:
            file_path = file_info['path']
            file_content = file_info['content']

            # Truncate very long files
            if len(file_content) > 3000:
                file_content = file_content[:3000] + "\n\n... (truncated)"

            file_contents.append(f"FILE: {file_path}\n```python\n{file_content}\n```\n")

        # Build the full prompt
        prompt = f"""You are a code analysis assistant. Analyze the following GitHub repository files and provide a simple, clear explanation of what this project does.

Please explain:
1. What is the main purpose of this project?
2. What technology stack does it use?
3. How does it work (high-level overview)?
4. What are the key features or components?
5. Any important notes or requirements?

Keep the explanation simple and accessible to someone who may not be familiar with all the technical details.

Here are the repository files:

{chr(10).join(file_contents)}

Provide your explanation in a friendly, conversational tone. Keep it under 500 words if possible."""

        return prompt

    def check_model_available(self) -> bool:
        """
        Check if the configured Groq model is available.

        Returns:
            True if model is available, False otherwise.
        """
        try:
            if not self._has_api_key:
                return False
            response = httpx.get(
                f'{self.host}/models/{self.model}',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15.0,
            )
            return response.is_success
        except Exception as e:
            print(f"Model check failed: {e}")
            return False

    def list_models(self) -> List[str]:
        """
            List available models on Groq.

        Returns:
            List of available model names.
        """
        try:
            if not self._has_api_key:
                return []
            response = httpx.get(
                f'{self.host}/models',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15.0,
            )
            response.raise_for_status()
            return [item['id'] for item in response.json().get('data', [])]
        except Exception as e:
            print(f"Error listing Groq models: {e}")
            return []
