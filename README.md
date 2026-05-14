# AI Pair Programmer

CLI tool that sends your **current unstaged + staged changes vs `HEAD`** (`git diff HEAD`) to a language model and prints a structured code review: summary, risks, suggestions, and an optional unified diff patch. The goal is to surface issues early, similar to having another developer glance at the diff before you ship.

## What it does

1. Reads the diff from the Git repo in the **current working directory** (`.`).
2. Truncates the diff to **10,000 characters** if it is longer (to stay within typical context limits).
3. Calls the configured backend with a fixed prompt that asks for **JSON only** (no chat).
4. Renders the result in the terminal with [Rich](https://github.com/Textualize/rich): panels for summary, bullet lists for risks and suggestions, and syntax-highlighted diff if a patch is returned.

## Requirements

- **Git** repository (the tool uses [GitPython](https://gitpython.readthedocs.io/)).
- **Python 3** and a virtual environment. This repo expects a **`.venv` in the project root** (create one if needed: `python -m venv .venv`).

  Install dependencies into that environment:

  ```bash
  .venv/bin/pip install -r requirements.txt
  ```

  Run the CLI with the same interpreter, for example:

  ```bash
  .venv/bin/python main.py --model mock
  ```

  If you prefer activation: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows), then `pip install -r requirements.txt` and `python main.py`.

## Backends and configuration

| Mode | When | Model flag (`--model`) | Extra setup |
|------|------|------------------------|-------------|
| **Mock** (default) | `--model mock` or omit `--model` (default is `mock`) | Ignored for real inference; uses built-in fake output | None |
| **OpenRouter** | `--model` is **not** `mock` and **`--local` is not set** | OpenRouter model id, e.g. `openai/gpt-4o-mini` | Set `OPENROUTER_API_KEY` |
| **Ollama (local)** | **`--local`** | Ollama model name, e.g. `qwen2.5:7b` (see `OllamaLocalProvider` in `providers.py`) | [Ollama](https://ollama.com/) running locally; Python `ollama` client |

- **`OPENROUTER_API_KEY`** — required for OpenRouter; read from the environment ([OpenRouter API](https://openrouter.ai/docs)).
- **Ollama** — no API key in code; relies on your local Ollama daemon and installed models.

**Note:** The CLI accepts `--provider` (default `openrouter`), but **`main.py` does not branch on it** today: non-mock, non-local runs always use `OpenRouterProvider`.

## Usage

Run from the root of a Git repo (or any path where `.` is a repo), using the project virtual environment:

```bash
.venv/bin/python main.py
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
.venv/bin/python main.py
.venv/bin/python main.py --model mock

# OpenRouter (set OPENROUTER_API_KEY first)
.venv/bin/python main.py --model anthropic/claude-3.5-sonnet

# Local Ollama
.venv/bin/python main.py --local --model qwen2.5:7b
```

## Expected model output

Backends are instructed to return JSON matching this shape (see `SYSTEM_PROMPT` in `providers.py`):

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

That data is rendered by Rich. A typical terminal session looks like this when you run `.venv/bin/python main.py --model mock`:

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
