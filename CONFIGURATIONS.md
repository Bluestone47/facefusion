# CONFIGURATIONS.md

This document explains how the selected `facefusion.ini` keys in `[paths]` and `[patterns]` are loaded and used.

## Scope

- `[paths]`: `temp_path`, `jobs_path`, `source_paths`, `target_path`, `output_path`
- `[patterns]`: `source_pattern`, `target_pattern`, `output_pattern`

## How Config Values Are Read

- Config file path is set by `--config-path` (default: `facefusion.ini`) in `facefusion/program.py`.
- Config values are loaded through `facefusion/config.py`.
- Empty values in `facefusion.ini` are treated as unset and fall back to command defaults (`get_*_value` returns fallback when `.strip()` is empty).

## Command Surface

- `run` and `headless-run` use explicit paths (`source_paths`, `target_path`, `output_path`).
- `batch-run` uses patterns (`source_pattern`, `target_pattern`, `output_pattern`).
- Job commands (`job-*`) consume `jobs_path` and (for step-producing commands) path-related step args.

## [paths]

### temp_path

- CLI/config key: `--temp-path` / `[paths].temp_path`
- Default: `tempfile.gettempdir()`
- Applied to runtime state in `facefusion/args.py`.
- Used by `facefusion/temp_helper.py` to build temporary working directories:
  - `${temp_path}/facefusion/<target_file_name>/...`
- UI also sets `GRADIO_TEMP_DIR` to `${temp_path}/gradio` in `facefusion/uis/core.py`.

### jobs_path

- CLI/config key: `--jobs-path` / `[paths].jobs_path`
- Default: `.jobs`
- `facefusion/jobs/job_manager.py:init_jobs()` creates status subdirectories under this path (`drafted`, `queued`, `failed`, `completed`).
- Used by job lifecycle commands and runners to locate/write job JSON files.

### source_paths

- CLI/config key: `-s/--source-paths` / `[paths].source_paths`
- Type: list (`nargs='+'` in CLI; whitespace-split in config parser).
- Represents source media inputs for non-batch processing.
- Stored as step args and consumed by processors/workflows.

### target_path

- CLI/config key: `-t/--target-path` / `[paths].target_path`
- Represents the input media to be processed.
- In `facefusion/core.py`, processing path is selected by target type:
  - image target -> image workflow
  - video target -> video workflow

### output_path

- CLI/config key: `-o/--output-path` / `[paths].output_path`
- Represents the final output file path.
- Processors commonly validate output path constraints before processing:
  - output directory must exist (`in_directory(output_path)`)
  - output extension must match target extension (`same_file_extension(target_path, output_path)`)

## [patterns] (batch-run)

### source_pattern

- CLI/config key: `-s/--source-pattern` / `[patterns].source_pattern`
- Expanded via `resolve_file_pattern()` in `facefusion/filesystem.py`.
- Important: pattern must include a valid directory component because `resolve_file_pattern()` first checks `in_directory(pattern)`.
  - Works: `./images/*.jpg`, `/abs/path/*.png`
  - Does not resolve: `*.jpg` (no directory component)

### target_pattern

- CLI/config key: `-t/--target-pattern` / `[patterns].target_pattern`
- Expanded the same way as `source_pattern`.
- `batch-run` requires matching targets to create steps.

### output_pattern

- CLI/config key: `-o/--output-pattern` / `[patterns].output_pattern`
- Template string used in `facefusion/core.py:process_batch()` with `str.format(...)`.
- Placeholder sets used by code:
  - source + target mode: `{index}`, `{source_name}`, `{target_name}`, `{target_extension}`
  - target-only mode: `{index}`, `{target_name}`, `{target_extension}`
- If a referenced placeholder name does not exist, code catches `KeyError` and returns failure.
- In practice, `output_pattern` should always be set for `batch-run`.

## Batch Expansion Behavior

- With both source and target patterns: steps are generated from the Cartesian product of all resolved source/target files (`itertools.product`).
- With target pattern only: one step per resolved target.

## Practical Examples

- Target-only batch:
  - `--target-pattern ./frames/*.jpg`
  - `--output-pattern ./out/frame-{index}.{target_extension}`
- Source-to-target batch:
  - `--source-pattern ./sources/*.jpg`
  - `--target-pattern ./targets/*.mp4`
  - `--output-pattern ./out/{source_name}-to-{target_name}-{index}.{target_extension}`

## Key Pitfalls

- Empty config values are ignored, so defaults may apply silently.
- Pattern strings without a directory component are not expanded.
- Mismatched or missing `output_pattern` placeholders fail `batch-run` step generation.
