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

PATCH_MODE=$(choose_patch_mode)
if [[ -z "$PATCH_MODE" ]]; then
    PATCH_MODE="Latest"
fi

detect_patches

CONFIRM_PATCHING=$(confirm_patching)
if [[ "$CONFIRM_PATCHING" != "Patch" ]]; then
    exit 0
fi

echo "=> [1/5] Creating backup of Half-Life installation..."
if [ "$BACKUP_HL" = true ]; then
  DATE=$(date +"%Y-%m-%d")
  DEST="$HOME/Documents/Half-Life backup ($DATE)"
  cp -a "$HL_FOLDER" "$DEST" || exit 1
  echo "Backup complete."
fi

echo "=> [2/5] Preparing environment..."
if [ -d "$WORKING_DIR" ]; then
    rm -rf "$WORKING_DIR" || exit 1
fi

mkdir -p "$WORKING_DIR" || exit 1
prepare_env

echo "=> [3/5] Preparing components..."
if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then prepare_goldsrc; fi

REF_HLFIXED="hlfixed"
REF_OPFORFIXED="opforfixed"
REF_BSHIFT="bshift"
REF_DMC="dmc"

if [ "$PATCH_MODE" = "Stable" ]; then
    if [ -n "$STABLE_HLFIXED_COMMIT" ]; then REF_HLFIXED="$STABLE_HLFIXED_COMMIT"; fi
    if [ -n "$STABLE_OPFORFIXED_COMMIT" ]; then REF_OPFORFIXED="$STABLE_OPFORFIXED_COMMIT"; fi
    if [ -n "$STABLE_BSHIFT_COMMIT" ]; then REF_BSHIFT="$STABLE_BSHIFT_COMMIT"; fi
    if [ -n "$STABLE_DMC_COMMIT" ]; then REF_DMC="$STABLE_DMC_COMMIT"; fi
fi

# Enforce stable for DMC as latest is broken
if [ -n "$STABLE_DMC_COMMIT" ]; then REF_DMC="$STABLE_DMC_COMMIT"; fi

if [ "$HL_REQUIRES_PATCH" = true ]; then prepare_hlsdk_mod "hlfixed" "$REF_HLFIXED"; fi
if [ "$OPFOR_REQUIRES_PATCH" = true ]; then prepare_hlsdk_mod "opforfixed" "$REF_OPFORFIXED"; fi
if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then prepare_hlsdk_mod "bshift" "$REF_BSHIFT"; fi
if [ "$DMC_REQUIRES_PATCH" = true ]; then prepare_hlsdk_mod "dmc" "$REF_DMC"; fi
if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then prepare_cstrike; fi

echo "=> [4/5] Building components..."
if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then build_goldsrc; fi
if [ "$HL_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "hlfixed"; fi
if [ "$OPFOR_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "opforfixed"; fi
if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "bshift"; fi
if [ "$DMC_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "dmc"; fi
if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then build_cstrike; fi

echo "=> [5/5] Installing components..."
if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then install_goldsrc; fi
if [ "$HL_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-hlfixed"; fi
if [ "$OPFOR_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-opforfixed"; fi
if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-bshift"; fi
if [ "$DMC_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-dmc"; fi
if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then install_generic "cs16-client"; fi

echo "Patching complete!"
show_success