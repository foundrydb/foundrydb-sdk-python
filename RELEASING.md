# Releasing foundrydb (Python SDK)

## Prerequisites

Add the following secret to the GitHub repository (`Settings > Secrets and variables > Actions`):

| Secret name | Value |
|-------------|-------|
| `PYPI_API_TOKEN` | A PyPI API token with **Upload** permission for the `foundrydb` project. Create one at https://pypi.org/manage/account/token/. |

## Publishing a new version

1. Ensure `main` is in the state you want to release.
2. Create and push a version tag:

   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

3. The `Publish to PyPI` workflow triggers automatically. It patches the `version` field in `pyproject.toml` ephemerally (in CI only, never committed), builds both wheel and sdist via `python -m build`, then uploads with `twine`.

No source-file edits are needed prior to tagging.

## Manual trigger

You can also trigger the workflow manually from the GitHub Actions UI (`workflow_dispatch`) by supplying the tag name (e.g. `v1.2.3`).

## Build backend note

This project uses **hatchling** as the build backend. The CI workflow patches the `version =` line in `pyproject.toml` with `sed` before building, which is the most portable approach when hatch-vcs is not configured.
