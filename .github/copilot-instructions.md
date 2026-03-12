# Copilot Instructions

## Project context
This repository provides utilities for renaming, stacking, and processing photo files.

## Environment and dependencies
- Use `uv` for environment and dependency operations.
- Prefer commands: `uv sync`, `uv run python ...`, and `uv run pytest`.
- Avoid Conda-specific instructions in docs.

## Code style expectations
- Keep file-system mutations explicit and reversible where possible.
- Validate EXIF assumptions defensively before writing metadata.
- Keep GUI and non-GUI logic separated when practical.

## Testing expectations
- Add tests for filename/date transformations.
- Isolate image-processing logic from UI for unit tests.
