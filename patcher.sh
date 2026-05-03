#!/bin/bash

HLPATCHER_VERSION="3.0.0"

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
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt" || exit 1

echo "=> Starting HLPatcher..."
HLPATCHER_VERSION="$HLPATCHER_VERSION" "$VENV_DIR/bin/python3" -m patcher