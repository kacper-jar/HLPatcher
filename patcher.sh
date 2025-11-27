#!/bin/bash

VERSION="1.3.0"

WORKING_DIR="/tmp/HLPatcher"

HL_FOLDER=""

BACKUP_HL=false

GOLDSRC_REQUIRES_PATCH=false
HL_REQUIRES_PATCH=false
OPFOR_REQUIRES_PATCH=false
BSHIFT_REQUIRES_PATCH=false
DMC_REQUIRES_PATCH=false
CSTRIKE_REQUIRES_PATCH=false

CMAKE_NEEDED=false

source "$(dirname "$0")/modules/gui.sh"
source "$(dirname "$0")/modules/patches.sh"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "This script can only be run on macOS."
    exit 1
fi

function cleanup() {
    echo "Cleaning up..."
    if [ -d "$WORKING_DIR" ]; then
      rm -rf "$WORKING_DIR"
    fi
}

if ! xcode-select -p &>/dev/null; then
    show_no_cli_tools_error
    exit 1
fi

trap cleanup EXIT INT TERM

show_welcome "$VERSION"

HL_FOLDER=$(choose_hl_folder)
if [[ "$HL_FOLDER" == "CANCELLED" ]]; then
    exit 0
fi

if [[ ! -f "$HL_FOLDER/hl_osx" ]]; then
    echo "hl_osx file not found in $HL_FOLDER."
    invalid_hl_folder
    exit 1
fi

if [[ "$(backup_prompt)" == "Yes" ]]; then
    BACKUP_HL=true
fi

detect_patches

CONFIRM_PATCHING=$(confirm_patching)
if [[ "$CONFIRM_PATCHING" != "Patch" ]]; then
    exit 0
fi

if [ "$BACKUP_HL" = true ]; then
  DATE=$(date +"%Y-%m-%d")
  DEST="$HOME/Documents/Half-Life backup ($DATE)"
  cp -a "$HL_FOLDER" "$DEST" || exit 1
  echo "Backup complete."
fi

if [ -d "$WORKING_DIR" ]; then
    rm -rf "$WORKING_DIR" || exit 1
fi

echo "=> [1/3] Preparing..."
mkdir -p "$WORKING_DIR" || exit 1

prepare_common

if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then prepare_goldsrc; fi
if [ "$HL_REQUIRES_PATCH" = true ]; then prepare_hlsdk_mod "hlfixed" "hlfixed"; fi
if [ "$OPFOR_REQUIRES_PATCH" = true ]; then prepare_hlsdk_mod "opforfixed" "opforfixed"; fi
if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then prepare_hlsdk_mod "bshift" "bshift"; fi
if [ "$DMC_REQUIRES_PATCH" = true ]; then prepare_hlsdk_mod "dmc" "895b28d"; fi
if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then prepare_cstrike; fi

echo "=> [2/3] Building..."

if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then build_goldsrc; fi
if [ "$HL_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "hlfixed"; fi
if [ "$OPFOR_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "opforfixed"; fi
if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "bshift"; fi
if [ "$DMC_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "dmc"; fi
if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then build_cstrike; fi

echo "=> [3/3] Installing..."

if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then install_goldsrc; fi
if [ "$HL_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-hlfixed"; fi
if [ "$OPFOR_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-opforfixed"; fi
if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-bshift"; fi
if [ "$DMC_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-dmc"; fi
if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then install_generic "cs16-client"; fi

echo "Patching complete!"
show_success