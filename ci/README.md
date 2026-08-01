# ci/

GitHub Actions workflow definitions must live at `.github/workflows/` (a
GitHub platform requirement, not a project choice) -- see
`.github/workflows/ci.yml` for the actual CI pipeline.

This directory is reserved for CI-adjacent scripts and configuration that
aren't GitHub Actions YAML itself: things a workflow step might call out to,
or configuration for a future non-GitHub CI system.
