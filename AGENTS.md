# AGENTS.md

This file helps coding agents work effectively in this repository.

## Project Snapshot

- FaceFusion is a Python CLI-first face manipulation platform.
- Entrypoints:
  - `facefusion.py` starts the main CLI (`conda.setup()` then `core.cli()`).
  - `install.py` runs the installer CLI.
- Main package: `facefusion/`
- Tests: `tests/`

See also: [README.md](README.md)

## Internal References

- Paths and patterns behavior (selected `facefusion.ini` keys): [CONFIGURATIONS.md](CONFIGURATIONS.md)

## Fast Start Commands

- Install runtime dependencies:
  - `python install.py --onnxruntime default --skip-conda`
- Install dev/test tools used in CI:
  - `pip install pytest flake8 flake8-import-order mypy`
- Run tests:
  - `pytest`
- Run linting:
  - `flake8 facefusion.py install.py`
  - `flake8 facefusion tests`
- Run type checks:
  - `mypy facefusion.py install.py`
  - `mypy facefusion tests`

Source of truth for CI commands: [.github/workflows/ci.yml](.github/workflows/ci.yml)

## Architecture Map

- CLI routing and flow orchestration live in `facefusion/core.py`.
- Global runtime configuration is coordinated by `facefusion/state_manager.py`.
- Command argument normalization/reduction lives in `facefusion/args.py`.
- Job lifecycle logic is under `facefusion/jobs/`.
- Media pipeline helpers (ffmpeg, temp files, filesystem) are in:
  - `facefusion/ffmpeg.py`
  - `facefusion/ffmpeg_builder.py`
  - `facefusion/temp_helper.py`
  - `facefusion/filesystem.py`
- Processor modules are discovered dynamically from `facefusion/processors/`.

## Code Conventions (Important)

- Indentation is tabs (not spaces). Follow `.editorconfig`.
- Keep import order and style compatible with flake8 config.
- Maintain mypy strictness conventions already configured in `mypy.ini`.
- Prefer small, typed helper functions and project utility modules over ad-hoc logic.
- Do not rename public CLI commands or change argument semantics unless explicitly requested.

Style/config references:
- [.editorconfig](.editorconfig)
- [.flake8](.flake8)
- [mypy.ini](mypy.ini)

## Testing Notes and Pitfalls

- Many tests download assets from GitHub/Hugging Face at runtime.
- Tests assume `ffmpeg` is installed and available in `PATH`.
- Core pre-checks also expect `curl` in `PATH`.
- Several tests write to temp directories via `tempfile.gettempdir()`.
- In CI, encoder expectations are narrower (for example audio/video encoder set in ffmpeg tests).

If tests fail unexpectedly, first verify network access and local `ffmpeg`/`curl` availability.

## Safe Change Guidelines for Agents

- Prefer targeted fixes; avoid broad refactors across many processor modules in one change.
- When changing CLI or state behavior, update/add focused tests under `tests/test_cli_*.py` or relevant unit tests.
- Preserve existing command flow in `facefusion/core.py` unless task explicitly requires rerouting.
- Keep cross-platform behavior in mind (CI runs on macOS, Ubuntu, and Windows).

## Suggested Next Customizations

- Create a dedicated skill for CLI/job workflows (`/create-skill`) that standardizes patterns for editing `facefusion/core.py` and `facefusion/jobs/*`.
- Create a test-runner prompt (`/create-prompt`) for choosing fast unit subsets vs full media pipeline tests.
- Create a processor-module instruction (`/create-instruction`) scoped to `facefusion/processors/**` to enforce module interface consistency.
