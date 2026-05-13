from git import Repo

def extract_diff(repo_path):
    repo = Repo(repo_path)
    diff = repo.git.diff("HEAD")
    return diff

def run_mock_model(prompt):
    if "diff" in prompt.lower():
        return {
            "summary": "Detected code changes in repository.",
            "risks": ["Large diff may exceed context limits"],
            "suggestions": ["Break diff into per-file chunks"]
        }
    return {"summary": "No changes detected", "risks": [], "suggestions": []}

def build_prompt(diff: str) -> str:
    return f"""
You are an automated code review system.

You analyze git diffs and return structured JSON output.
You do not chat. You do not explain your reasoning outside the schema.

You MUST return ONLY valid JSON.

Do not include:
- markdown
- backticks
- explanations
- extra keys

Your output must match this schema exactly:

{{
  "summary": string,
  "risks": string[],
  "suggestions": string[],
  "patch": string | null
}}

Rules:
- summary must be 1–3 sentences
- risks must be specific and actionable
- suggestions must be concrete improvements, not vague advice
- patch must be a unified diff or null
- if unsure, prefer empty arrays rather than guessing

Analyze the following git diff:

<<<DIFF_START
{diff}
DIFF_END

Return a code review of the above diff.
"""

if __name__ == "__main__":
    repo_path = "."
    diff = extract_diff(repo_path)
    prompt = build_prompt(diff)
    result = run_mock_model(prompt)
    print(result)

