# AGENTS.md

This file provides guidance to AI coding assistants when working with code in this repository.

## Project Overview

TOML Kit is a style-preserving TOML library for Python. It parses TOML into a document model that keeps comments, whitespace, and ordering, so documents can be edited and re-serialized without losing formatting.

## Key Modules

- `tomlkit/api.py`: Public API (`parse`, `loads`, `dumps`, `document`, item constructors)
- `tomlkit/parser.py`: TOML parser producing `TOMLDocument`
- `tomlkit/container.py`: `Container` and out-of-order table proxies
- `tomlkit/items.py`: Item types (`Table`, `AoT`, `Array`, `String`, `Integer`, ...)
- `tomlkit/toml_document.py`, `tomlkit/toml_file.py`: Document and file wrappers

## Development Commands

```bash
# Install development dependencies
uv sync

# Run tests
uv run pytest

# Lint, format and type check
pre-commit run --all-files
uv run mypy
```

## Contribution Guidelines

### Duplicate Check

Before opening a PR, search the open PRs (e.g. `gh pr list --state open --search "<keywords>"`) for one that already fixes the same issue. If an existing PR's fix is valid, do not open a new one; report the existing PR instead. Fill in the PR template, including the Agent Drafting Metadata section.

### Human Attestation (Required for All PRs)

Every pull request MUST pass Human Attestation before it can be merged. AI assistants may help write code, but a human contributor is accountable for every change.

- A human MUST personally review the full diff, understand it, and confirm it is correct and intended before the PR is opened or marked ready for review.
- The human attests in the PR description that they have reviewed and take responsibility for the changes. PRs without this attestation will not be merged.
- AI assistants MUST NOT open, mark ready, approve, or merge a PR on their own, and MUST NOT write or check the attestation on the human's behalf. Stop and hand off to the human for attestation.
- Do not use automation to bypass, fake, or skip the Human Attestation check.
