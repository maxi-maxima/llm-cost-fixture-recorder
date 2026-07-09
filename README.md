# llm-cost-fixture-recorder

Record deterministic LLM cost fixtures so teams can catch pricing regressions in CI.

## Pain Point

AI agents, MCP servers, cost controls, release gates, and creator workflows are moving fast, but many teams still lack tiny local tools that can be dropped into CI or run from a terminal without shipping private data to another SaaS product.

## Why Now

June 2026 trend research showed strong momentum around MCP as the agent integration standard, CLI-first coding agents, verification bottlenecks, agent security controls, practical cost governance, and content automation. This project targets one of those high-signal operational gaps with a small auditable utility.

## Install

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows Git Bash
pip install -e .
```

No runtime dependencies are required beyond Python's standard library.

## Run

```bash
python -m llm_cost_fixture_recorder examples/calls.csv --budget 0.05
python -m llm_cost_fixture_recorder examples/calls.csv --warn-budget 0.03 --budget 0.05
python -m llm_cost_fixture_recorder examples/calls.csv --prices-json prices.json --strict-models
python -m llm_cost_fixture_recorder examples/calls.csv --json > current-costs.json
python -m llm_cost_fixture_recorder examples/calls.csv --baseline-json baseline-costs.json --max-increase 0.01
```

Use `--warn-budget` for soft CI alerts before enforcing a hard `--budget` failure. Use `--baseline-json` with a previous `--json` report to show the exact cost delta in reviews; add `--max-increase` to fail CI when fixture cost drift exceeds the allowed USD increase.
Both text and JSON output now include per-model totals so reviewers can quickly
see which model family is responsible for a fixture cost change.

CSV input must include `model`, `prompt_tokens`, and `completion_tokens`. Invalid
fixtures now fail with exit code `5` and a row-specific diagnostic instead of a
Python traceback, which makes CI failures easier to act on.

Custom price files let teams pin model rates in CI when providers change pricing or when internal gateway aliases do not match the built-in table:

```json
{
  "my-model": {"input_per_million": "0.25", "output_per_million": "1.00"}
}
```

## Example Output

Run the command above against files in `examples/` to see deterministic output suitable for demos, issue reports, and CI logs.

## Self Check

```bash
python -m unittest discover -s tests
```

## Roadmap

- Add richer machine-readable output for CI annotations.
- Add more real-world fixtures from popular agent and MCP workflows.
- Publish packaged binaries for users without Python environments.
- Add GitHub Action examples for pull-request automation.

## License

MIT
