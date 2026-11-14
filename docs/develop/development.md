# Development

Requirements: Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

## Setup

```bash
git clone https://github.com/pamagister/asciicade.git
cd asciicade
uv sync --all-groups
```

## Common tasks

| Command | Purpose |
|---|---|
| `make test` | Ruff, mypy, pytest and coverage |
| `make lint` | Ruff and mypy only |
| `make fmt` | Format and apply safe lint fixes |
| `make build` | Build the source distribution and wheel |
| `make validate` | Build and run `twine check` |
| `make precommit` | Format, lint and test |
| `make docs` | Build the Sphinx documentation |
| `make linkcheck` | Check external documentation links |

Run a single test file:

```bash
uv run pytest tests/test_snake_engine.py -v
```

## Documentation

`docs/index.md` is the source for `README.md`. After editing it, run:

```bash
make syncdocs
```

The documentation is built with Sphinx and the
[Sphinx Book Theme](https://sphinx-book-theme.readthedocs.io/). `make docs` treats warnings as
errors, so broken internal links and missing pages fail the build.

Releases are created by tagging a commit:

```bash
make release
```

Pushing a tag triggers the release workflow, which runs the full quality gate, builds and validates
the distributions, creates a GitHub release and publishes to PyPI using Trusted Publishing (OIDC).

See [Architecture](architecture.md) for the code layout and extension points.