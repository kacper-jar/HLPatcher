# Contributing

Thank you for your interest in contributing to **HLPatcher**! We appreciate your help in making classic Valve games
accessible on modern ARM Macs. This guide will help you get started with setting up your development environment,
making changes and submitting a pull request.

## Getting Started

### Fork the Repository

First, create a fork of the [HLPatcher repository](https://github.com/kacper-jar/HLPatcher) on GitHub. This gives you
your own copy of the project to work on.

### Clone Your Fork

Clone your forked repository to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/HLPatcher.git
cd HLPatcher
```

### Set Up Development Environment

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the runtime and development dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Project Structure

Here is a quick overview of the project's structure to help you navigate the codebase:

- `.github/`: GitHub Actions workflows and issue templates.
    - `workflows/tests.yml`: Runs the full test suite on every push and pull request to `main`.
    - `workflows/commitlint.yml`: Validates commit messages against Conventional Commits.
    - `workflows/release.yml`: Triggered on a tag push - runs tests, creates a ZIP archive, and opens a draft GitHub Release.
    - `workflows/docs.yml`: Builds and deploys MkDocs documentation.
- `data/`: Game data, patches, guides, and localization files.
    - `fixes/`: Game-specific patch scripts and binary fixes applied during the patching process.
    - `guides/`: Game downgrade guides shown to the user (JSON format).
    - `locales/`: Translation files for each supported language.
    - `components.json`: Game component definitions used by the patcher.
    - `locales.json`: Language mappings.
- `docs/`: Documentation source files (MkDocs + Material theme).
- `patcher/`: Main application source code.
    - `patcher.core`: Core logic - game detection, patching, models, i18n, update checker, and pipeline.
    - `patcher.ui`: CustomTkinter-based GUI - pages, navigation, router, and base components.
- `tests/`: Unit and integration tests (pytest).
    - `tests/core/`: Tests for game detection, patching logic, i18n, and models.
    - `tests/ui/`: Tests for UI pages.
- `patcher.sh`: Bootstrap shell script - sets up the virtual environment and launches the app.
- `crowdin.yml`: Crowdin localization configuration.
- `commitlint.config.js`: Commit message linting rules.
- `mkdocs.yml`: MkDocs documentation configuration.
- `requirements.txt`: Runtime dependencies.
- `requirements-dev.txt`: Development dependencies.

## Running Locally

Ensure your virtual environment is activated, then run the bootstrap script:

```bash
./patcher.sh
```

This will install any missing dependencies and launch the HLPatcher UI.

!!! tip "Debug Mode"
    You can launch HLPatcher in debug mode by passing the `debug` argument to `patcher.sh`:
    ```bash
    ./patcher.sh debug
    ```
    This can be helpful when troubleshooting patching-related issues.

## Testing Changes

### Automated Testing

We use `pytest` for testing. Tests run on **macOS** (matching the CI environment). Run the full suite with:

```bash
pytest
```

This will also generate a coverage report for the `patcher/` package. The configuration is defined in `pytest.ini`.

!!! important
    All tests must pass before a Pull Request can be merged. The CI pipeline runs the test suite automatically on every PR targeting `main`.

If you are adding a new feature, please add tests to cover it.

### Manual Testing

To test patches against actual game files, you can use the [HLPatcher Test Environment Builder](https://github.com/kacper-jar/HLPatcher-test-env-builder) tool. It automatically downloads and sets up clean testing environments by fetching games directly via Steam, eliminating the need to manually download games through the Steam client.

!!! important "Steam Account Prerequisites & Login Flow"
    - You must sign in with a Steam account that already owns all the games you intend to download.
    - The internal downloading tool does not keep you logged in between tasks. As a result, you will need to scan a new QR code with your Steam mobile app for each individual game as it begins downloading.

#### Getting Started

Clone the repository and install the dependencies:

```bash
git clone https://github.com/kacper-jar/HLPatcher-test-env-builder.git
cd HLPatcher-test-env-builder
python3 -m pip install -r requirements.txt
```

Then run the builder:

```bash
python3 builder.py
```

#### Workflow

The builder will guide you through the following steps in a terminal UI:

1. **Target directory** – Enter the path where the test environment should be created.
2. **Preset selection** – Choose a preset that determines which games to download.
3. **Summary** – Review the components that will be installed.
4. **Installation** – The builder downloads game files via Steam, authenticating with QR codes as needed, and merges everything into the target directory.

Once the environment is ready, point HLPatcher at the target directory to test your patches.

## Commit Message Convention

We follow the **Conventional Commits** style to keep the commit history readable.

Each commit message should follow this format:

```
<type>: <short description>
```

### Common Types

| Type         | Description                              | Example                                          |
|:-------------|:-----------------------------------------|:-------------------------------------------------|
| **feat**     | A new feature                            | `feat: add Half-Life 2 support`                  |
| **fix**      | A bug fix                                | `fix: prevent crash when steam path is missing`  |
| **docs**     | Documentation only changes               | `docs: update installation guide`                |
| **style**    | Code style changes (formatting, etc.)    | `style: reformat patcher.py with Black`          |
| **refactor** | Refactoring without changing behavior    | `refactor: extract game detection into helper`   |
| **perf**     | Performance improvements                 | `perf: reduce GoldSrc build time`                |
| **test**     | Adding or updating tests                 | `test: add regression tests for source engine`   |
| **build**    | Changes to build scripts or dependencies | `build: upgrade customtkinter to 5.2.2`          |
| **ci**       | Changes to CI configuration              | `ci: add coverage upload step to tests workflow` |
| **chore**    | Other changes                            | `chore: update license year`                     |
| **revert**   | Reverts a previous commit                | `revert: feat: add Half-Life 2 support`          |

### Tips for Good Commit Messages

- Keep it under 72 characters.
- Use the imperative mood: "add support" not "added support".
- Explain *what* changed and *why*, not *how*.

## Submitting a Pull Request

1. Create a new branch for your change: `git checkout -b feat/my-feature`.
2. Make your changes and test them locally.
3. Commit following the [Commit Message Convention](#commit-message-convention).
4. Push your branch: `git push origin feat/my-feature`.
5. Open a Pull Request against the `main` branch.
6. Provide a clear description of what you changed and why.

!!! note
    All test cases must pass in order for the Pull Request to be merged.

We will review your PR and provide feedback. Thank you for contributing!
