"""
FAULTLINE Provider-Agnostic LLM Client.
Supports Anthropic, OpenAI, Gemini, and a deterministic offline Mock/Cached provider
for benchmark reproducibility and zero-failure live demos.
"""

import os
import json
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel

DEFAULT_PROVIDER = os.environ.get("FAULTLINE_LLM_PROVIDER", "mock")

class LLMClient:
    def __init__(self, provider: str = DEFAULT_PROVIDER):
        self.provider = provider.lower()
        self._init_backend()

    def _init_backend(self):
        if self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        elif self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        elif self.provider == "gemini":
            from google import genai
            self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        else:
            self.provider = "mock"
            self.client = None

    def invoke_structured(
        self,
        agent_name: str,
        system_prompt: str,
        user_message: str,
        output_schema: Type[BaseModel],
        mock_response: Optional[Dict[str, Any]] = None
    ) -> BaseModel:
        """
        Executes a structured output invocation.
        In 'mock' mode or during automated benchmarks with fixed seeds,
        returns the deterministic schema directly.
        """
        if self.provider == "mock" or mock_response is not None:
            if mock_response is not None:
                return output_schema.model_validate(mock_response)
            return output_schema.model_validate({})

        if self.provider == "openai":
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o" if "commander" in agent_name or "remediator" in agent_name else "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format=output_schema,
            )
            return completion.choices[0].message.parsed

        elif self.provider == "anthropic":
            # Anthropic tool-based structured output
            tool_spec = {
                "name": output_schema.__name__,
                "description": f"Structured decision output for {agent_name}",
                "input_schema": output_schema.model_json_schema()
            }
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219" if "commander" in agent_name or "remediator" in agent_name else "claude-3-5-haiku-20241022",
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                tools=[tool_spec],
                tool_choice={"type": "tool", "name": output_schema.__name__}
            )
            for block in response.content:
                if block.type == "tool_use" and block.name == output_schema.__name__:
                    return output_schema.model_validate(block.input)
            raise ValueError(f"Failed to parse structured output from Anthropic response: {response}")

        elif self.provider == "gemini":
            response = self.client.models.generate_content(
                model="gemini-2.5-pro" if "commander" in agent_name or "remediator" in agent_name else "gemini-2.5-flash",
                contents=f"System: {system_prompt}\nUser: {user_message}",
                config={"response_mime_type": "application/json", "response_schema": output_schema}
            )
            return output_schema.model_validate_json(response.text)

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
