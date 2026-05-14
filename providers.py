from ollama import chat

import os
import json
import requests



SYSTEM_PROMPT = """
You are an automated code review system.

You analyze git diffs and return structured JSON output.

You do not chat.
You do not explain reasoning outside the schema.

You MUST return ONLY valid JSON.

Do not include:
- markdown
- backticks
- explanations
- extra keys

Your output must match this schema exactly, do not wrap JSON in markdown code fences:

{
  "summary": string,
  "risks": string[],
  "suggestions": string[],
  "patch": string | null
}

Rules:
- summary must be 1-3 sentences
- risks must be specific and actionable
- suggestions must be concrete improvements
- patch must be a unified diff or null
- prefer empty arrays over guessing
"""

REQUIRED_KEYS = [
    "summary",
    "risks",
    "suggestions",
    "patch"
]

def clean_json_response(content: str) -> str:
    content = content.strip()

    if content.startswith("```json"):
        content = content[len("```json"):]

    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


class ModelProvider:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement this method")

class MockProvider(ModelProvider):
    def generate(self, prompt: str) -> str:
        if "diff" in prompt.lower():
            return {
                "summary": "Detected code changes in repository.",
                "risks": ["Large diff may exceed context limits"],
                "suggestions": ["Break diff into per-file chunks"]
            }


class OpenRouterProvider:
    def __init__(self, model: str = "openrouter/owl-alpha"):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

    def generate(self, prompt: str):
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2
            }
        )

        # response.raise_for_status()
        if not response.ok:
            print(response.status_code)
            print(response.text)
            response.raise_for_status()
        data = response.json()
        print(data)
        content = data["choices"][0]["message"]["content"]
        cleaned = clean_json_response(content)

        missing = [k for k in REQUIRED_KEYS if k not in cleaned]
        if missing:
            raise ValueError(f"Missing keys: {missing}")
        return json.loads(cleaned)

class OllamaLocalProvider:
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model

    def generate(self, prompt: str):
        response = chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=False,
            options={"temperature": 0.2}
        )

        content = response["message"]["content"]

        # Parse JSON (will raise if model breaks format)
        return json.loads(content)
