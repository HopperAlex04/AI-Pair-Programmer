from git import Repo
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import providers

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
    repo_path = "."
    diff = extract_diff(repo_path)
    if len(diff) > MAX_DIFF_LENGTH:
        diff = diff[:MAX_DIFF_LENGTH]
    prompt = build_prompt(diff)
    provider = providers.OpenRouterProvider()
    result = provider.generate(prompt)
    render(result)

