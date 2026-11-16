# Changelog

## 2026-11-16

- Moved the example into `src/analyses/window_count/main.py`, separate from
  the shared runner and settings. Register additional analyses in `ANALYSES`.
- Results now go under `results/<analysis-name>/run-.../result.json`.
  The shared runner opens the IFC once for the registered analyses.

- Initial starter: count IFC windows using an import-safe callable function.
- Added a local runner that writes JSON to a new folder on each run.
- Added `src/settings.py` for the local model path, keeping setup separate from
  the analysis. A command-line path can still override it.
- No automatic publishing, run metadata or engineering assessment.

Add dated entries for your meaningful changes and explain their effect on the
receiving team. Routine executions do not need changelog entries.
