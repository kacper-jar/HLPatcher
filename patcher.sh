#!/bin/bash

HLPATCHER_VERSION="3.3.3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

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

PYTHON_ARCHIVE_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20260623/cpython-3.14.6+20260623-aarch64-apple-darwin-install_only.tar.gz"
PYTHON_ARCHIVE="cpython-3.14.6+20260623-aarch64-apple-darwin-install_only.tar.gz"
PYTHON_ARCHIVE_SHA256="44f31db9afd16f714194580f2362e66d8b1784bf3a3e2d0ac86e7b392f32d75b"
PYTHON_DIR="$SCRIPT_DIR/.python"
PYTHON_BIN="$PYTHON_DIR/python/bin/python3"
DOWNLOAD_DIR="$PYTHON_DIR/download"

if [ ! -x "$PYTHON_BIN" ]; then
    rm -rf "$PYTHON_DIR"
    mkdir -p "$DOWNLOAD_DIR"
    echo "=> Downloading standalone Python..."
    curl -fL -o "$DOWNLOAD_DIR/$PYTHON_ARCHIVE" "$PYTHON_ARCHIVE_URL" || exit 1
    if ! echo "$PYTHON_ARCHIVE_SHA256  $DOWNLOAD_DIR/$PYTHON_ARCHIVE" | shasum -a 256 -c -s -; then
        echo "The standalone Python download is corrupted. Please run HLPatcher again."
        exit 1
    fi
    echo "=> Extracting standalone Python..."
    tar -xzf "$DOWNLOAD_DIR/$PYTHON_ARCHIVE" -C "$DOWNLOAD_DIR" || exit 1
    mv "$DOWNLOAD_DIR/python" "$PYTHON_DIR/python" || exit 1
    rm -rf "$DOWNLOAD_DIR"
fi

HLPATCHER_BIN="$PYTHON_DIR/python/bin/HLPatcher"
if [ ! -x "$HLPATCHER_BIN" ]; then
    echo "=> Creating HLPatcher link to standalone Python..."
    ln -f "$PYTHON_DIR/python/bin/python3.14" "$HLPATCHER_BIN"
fi

echo "=> Installing dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r "$SCRIPT_DIR/requirements.txt" || exit 1

HLPATCHER_DEBUG="0"
for arg in "$@"; do
    if [ "$arg" = "debug" ]; then
        echo "Debug mode enabled."
        "$PYTHON_BIN" -m pip install -r "$SCRIPT_DIR/requirements-dev.txt" || exit 1
        HLPATCHER_DEBUG="1"
    fi
done

echo "=> Starting HLPatcher..."
HLPATCHER_DEBUG="$HLPATCHER_DEBUG" HLPATCHER_VERSION="$HLPATCHER_VERSION" "$HLPATCHER_BIN" -m patcher
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