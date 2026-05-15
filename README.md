# eppy

**eppy** is a CLI that sends your **current unstaged + staged changes vs `HEAD`** (`git diff HEAD`) to a language model and prints a structured code review: summary, risks, suggestions, and an optional unified diff patch. The goal is to surface issues early, similar to having another developer glance at the diff before you ship.

## What it does

1. Reads the diff from the Git repo in the **current working directory** (`.`).
2. Truncates the diff to **10,000 characters** if it is longer (to stay within typical context limits).
3. Calls the configured backend with a fixed prompt that asks for **JSON only** (no chat).
4. Renders the result in the terminal with [Rich](https://github.com/Textualize/rich): panels for summary, bullet lists for risks and suggestions, and syntax-highlighted diff if a patch is returned.

## Install

You need **[pipx](https://pipx.pypa.io/)** and **Python 3.11+**. Then install **eppy** from GitHub into an isolated environment:

```bash
pipx install git+https://github.com/HopperAlex04/AI-Pair-Programmer.git
```

That installs the `eppy` command on your `PATH`. Try it from any Git repo:

```bash
eppy --model mock
```

To upgrade after upstream changes:

```bash
pipx upgrade eppy
```

(If the install name differs, use `pipx list` and `pipx upgrade <name>`.)

## Requirements

- A **Git** repository to review (the tool runs `git diff HEAD` in the current directory).
- **Python 3.11+** and **pipx** for installation.
- For live models: **`OPENROUTER_API_KEY`** (OpenRouter) or a local **[Ollama](https://ollama.com/)** daemon (`--local`).

## Backends and configuration

| Mode | When | Model flag (`--model`) | Extra setup |
|------|------|------------------------|-------------|
| **Mock** (default) | `--model mock` or omit `--model` (default is `mock`) | Ignored for real inference; uses built-in fake output | None |
| **OpenRouter** | `--model` is **not** `mock` and **`--local` is not set** | OpenRouter model id, e.g. `openai/gpt-4o-mini` | Set `OPENROUTER_API_KEY` |
| **Ollama (local)** | **`--local`** | Ollama model name, e.g. `qwen2.5:7b` (see `OllamaLocalProvider` in `src/eppy/providers.py`) | [Ollama](https://ollama.com/) running locally |

- **`OPENROUTER_API_KEY`** — required for OpenRouter ([OpenRouter API](https://openrouter.ai/docs)).
- **Ollama** — no API key in code; relies on your local Ollama daemon and installed models.

**Note:** The CLI accepts `--provider` (default `openrouter`), but **`src/eppy/cli.py` does not branch on it** today: non-mock, non-local runs always use `OpenRouterProvider`.

## Usage

Run from the root of a Git repo (or any path where `.` is a repo):

```bash
eppy
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model TEXT` | `mock` | Model id for OpenRouter or Ollama; use `mock` for offline placeholder output. |
| `--local` | off | Use **Ollama** instead of OpenRouter. |
| `--provider TEXT` | `openrouter` | Parsed only; routing is not implemented beyond OpenRouter vs Ollama vs mock. |

### Examples

```bash
# Offline placeholder review
eppy
eppy --model mock

# OpenRouter (set OPENROUTER_API_KEY first)
eppy --model anthropic/claude-3.5-sonnet

# Local Ollama
eppy --local --model qwen2.5:7b
```

## Expected model output

Backends are instructed to return JSON matching this shape (see `SYSTEM_PROMPT` in `src/eppy/providers.py`):

- **`summary`** — string, 1–3 sentences  
- **`risks`** — array of strings (specific, actionable)  
- **`suggestions`** — array of strings  
- **`patch`** — unified diff string or `null`

The mock provider may omit `patch`; the UI treats a missing patch as “no patch suggested.”

### Mock provider (`--model mock`)

When the prompt contains `"diff"` (it always does for a normal run), `MockProvider` returns this object (no `patch` key):

```json
{
  "summary": "Detected code changes in repository.",
  "risks": ["Large diff may exceed context limits"],
  "suggestions": ["Break diff into per-file chunks"]
}
```

That data is rendered by Rich. A typical terminal session looks like this when you run `eppy --model mock`:

```
──────────────────────────────── AI Code Review ────────────────────────────────
╭────────────────────────────────── Summary ───────────────────────────────────╮
│ Detected code changes in repository.                                         │
╰──────────────────────────────────────────────────────────────────────────────╯

Risks
• Large diff may exceed context limits

Suggestions
• Break diff into per-file chunks

No patch suggested
```

## Limitations

- Only **`git diff HEAD`** is reviewed (not arbitrary commits or branches).
- Large diffs are **hard-truncated** at 10,000 characters.
- OpenRouter responses are cleaned of common markdown fences; malformed JSON from the model will surface as parse errors.
