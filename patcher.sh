#!/bin/bash

HLPATCHER_VERSION="3.1.3"

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

PYTHON_ARCHIVE_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20260623/cpython-3.14.6+20260623-aarch64-apple-darwin-pgo+lto-full.tar.zst"
PYTHON_ARCHIVE="cpython-3.14.6+20260623-aarch64-apple-darwin-pgo+lto-full.tar.zst"
PYTHON_DIR="$SCRIPT_DIR/.python"
PYTHON_BIN="$PYTHON_DIR/python/install/bin/python3"

if [ ! -d "$PYTHON_DIR" ]; then
    echo "=> Downloading standalone Python..."
    mkdir -p "$PYTHON_DIR"
    curl -L -o "$SCRIPT_DIR/$PYTHON_ARCHIVE" "$PYTHON_ARCHIVE_URL" || exit 1
    echo "=> Extracting standalone Python..."
    tar -xf "$SCRIPT_DIR/$PYTHON_ARCHIVE" -C "$PYTHON_DIR" || exit 1
    rm "$SCRIPT_DIR/$PYTHON_ARCHIVE"
fi

if [ ! -x "$PYTHON_BIN" ]; then
    echo "Failed to find standalone Python at $PYTHON_BIN."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "=> Creating virtual environment..."
    "$PYTHON_BIN" -m venv "$VENV_DIR" || exit 1
fi

echo "=> Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" || exit 1

HLPATCHER_DEBUG="0"
for arg in "$@"; do
    if [ "$arg" = "debug" ]; then
        echo "Debug mode enabled."
        "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements-dev.txt" || exit 1
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