from git import Repo
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

import providers
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="AI Code Review")
    parser.add_argument("--model", type=str, required=False, default = "mock", help="Model to use")
    parser.add_argument("--local", action="store_true", required=False, default=False, help="Use local model through Ollama")
    parser.add_argument("--provider", type=str, required=False, default="openrouter", help="Provider to use (Will be ignored if --local is True)")
    return parser.parse_args()

def extract_diff(repo_path):
    repo = Repo(repo_path)
    diff = repo.git.diff("HEAD")
    return diff

def build_prompt(diff: str) -> str:
    return f"""
Analyze the following git diff.

<<<DIFF_START
{diff}
DIFF_END
"""

console = Console()

def render(result):
    console.rule("AI Code Review")

    # Summary
    console.print(Panel(result["summary"], title="Summary", style="cyan"))

    # Risks
    if result["risks"]:
        console.print("\n[bold yellow]Risks[/bold yellow]")
        for r in result["risks"]:
            console.print(f"• {r}")

    # Suggestions
    if result["suggestions"]:
        console.print("\n[bold green]Suggestions[/bold green]")
        for s in result["suggestions"]:
            console.print(f"• {s}")

    # Patch
    patch = result.get("patch")
    if patch:
        console.print("\n[bold blue]Proposed Patch[/bold blue]")
        console.print(Syntax(patch, "diff", theme="monokai"))
    else:
        console.print("\n[bold blue]No patch suggested[/bold blue]")


MAX_DIFF_LENGTH = 10000

if __name__ == "__main__":
    args = parse_args()
    repo_path = "."
    diff = extract_diff(repo_path)
    if len(diff) > MAX_DIFF_LENGTH:
        diff = diff[:MAX_DIFF_LENGTH]
    prompt = build_prompt(diff)
    if args.model == "mock":
        provider = providers.MockProvider()
    elif args.local:
        provider = providers.OllamaLocalProvider(args.model)
    else:
        provider = providers.OpenRouterProvider(args.model)
    result = provider.generate(prompt)
    render(result)

