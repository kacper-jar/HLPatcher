#!/bin/bash

HLPATCHER_VERSION="3.1.1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "HLPatcher Bootstrap ($HLPATCHER_VERSION)"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "This script can only be run on macOS."
    exit 1
fi

if ! xcode-select -p &>/dev/null; then
    echo "Xcode Command Line Tools not found."
    echo "Please install them by running: xcode-select --install"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "Python 3 is required but not found."
    echo "Please install Python 3 and try again."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "=> Creating virtual environment..."
    python3 -m venv "$VENV_DIR" || exit 1
fi

echo "=> Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" || exit 1

HLPATCHER_DEBUG="0"
for arg in "$@"; do
    if [ "$arg" = "debug" ]; then
        echo "Debug mode enabled."
        HLPATCHER_DEBUG="1"
    fi
done

echo "=> Starting HLPatcher..."
HLPATCHER_DEBUG="$HLPATCHER_DEBUG" HLPATCHER_VERSION="$HLPATCHER_VERSION" "$VENV_DIR/bin/python3" -m patcher
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "================================================================================"
    echo "                               HLPATCHER CRASHED                                "
    echo "================================================================================"
    echo " HLPatcher encountered an unexpected error while running and crashed."
    echo ""
    echo " To help fix this issue, please report it on GitHub by opening a new issue:"
    echo " -> https://github.com/kacper-jar/HLPatcher/issues/new?template=bug_patcher.md"
    echo ""
    echo " Important:"
    echo "  - Please copy and paste the ENTIRE terminal output above into the"
    echo "    \"Error Messages or Logs\" section of the report."
    echo "  - You will need a GitHub account to submit an issue."
    echo "================================================================================"
    exit $EXIT_CODE
fi