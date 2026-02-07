#!/bin/bash

VERSION="2.0.0"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
WORKING_DIR="/tmp/HLPatcher"

HL_FOLDER=""

BACKUP_HL=false

# GoldSrc related
GOLDSRC_REQUIRES_PATCH=false
HL_REQUIRES_PATCH=false
OPFOR_REQUIRES_PATCH=false
BSHIFT_REQUIRES_PATCH=false
DMC_REQUIRES_PATCH=false
CSTRIKE_REQUIRES_PATCH=false

# Source related
SOURCE_REQUIRES_PATCH=false
HLS_REQUIRES_PATCH=false
HL2_REQUIRES_PATCH=false
HL2LC_REQUIRES_PATCH=false
HL2EP_REQUIRES_PATCH=false

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

ENGINE_TYPE=$(choose_engine)
if [[ "$ENGINE_TYPE" == "Source" ]]; then
    show_source_legacy_warning
fi

HL_FOLDER=$(choose_hl_folder)
if [[ "$HL_FOLDER" == "CANCELLED" ]]; then
    exit 0
fi

EXPECTED_EXEC="hl_osx"
if [[ "$ENGINE_TYPE" == "Source" ]]; then
    EXPECTED_EXEC="hl2_osx"
fi

if [[ ! -f "$HL_FOLDER/$EXPECTED_EXEC" ]]; then
    echo "$EXPECTED_EXEC file not found in $HL_FOLDER."
    invalid_hl_folder "$EXPECTED_EXEC"
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

echo "=> [1/7] Creating backup of Half-Life installation..."
if [ "$BACKUP_HL" = true ]; then
  DATE=$(date +"%Y-%m-%d")
  DEST="$HOME/Documents/Half-Life backup ($DATE)"
  cp -a "$HL_FOLDER" "$DEST" || exit 1
  echo "Backup complete."
fi

echo "=> [2/7] Preparing environment..."
if [ -d "$WORKING_DIR" ]; then
    rm -rf "$WORKING_DIR" || exit 1
fi

mkdir -p "$WORKING_DIR" || exit 1
prepare_env

echo "=> [3/7] Preparing components..."
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

if [ "$SOURCE_REQUIRES_PATCH" = true ]; then prepare_source; fi

echo "=> [4/7] Patching components..."
if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then patch_generic "cs16-client"; fi

if [ "$SOURCE_REQUIRES_PATCH" = true ]; then patch_generic "source-engine"; fi

echo "=> [5/7] Building components..."
if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then build_goldsrc; fi
if [ "$HL_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "hlfixed"; fi
if [ "$OPFOR_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "opforfixed"; fi
if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "bshift"; fi
if [ "$DMC_REQUIRES_PATCH" = true ]; then build_hlsdk_mod "dmc"; fi
if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then build_cstrike; fi

if [ "$HLS_REQUIRES_PATCH" = true ]; then build_source "hl1"; fi
if [ "$HL2_REQUIRES_PATCH" = true -o "$HL2LC_REQUIRES_PATCH" = true ]; then build_source "hl2"; fi
if [ "$HL2EP_REQUIRES_PATCH" = true ]; then build_source "episodic"; fi

echo "=> [6/7] Installing components..."
if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then install_goldsrc; fi
if [ "$HL_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-hlfixed"; fi
if [ "$OPFOR_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-opforfixed"; fi
if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-bshift"; fi
if [ "$DMC_REQUIRES_PATCH" = true ]; then install_generic "hlsdk-portable-dmc"; fi
if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then install_generic "cs16-client"; fi

if [ "$SOURCE_REQUIRES_PATCH" = true ]; then install_source_all; fi
if [ "$HL2LC_REQUIRES_PATCH" = true ]; then install_lost_coast; fi

echo "=> [7/7] Fixing links..."
if [ "$SOURCE_REQUIRES_PATCH" = true ]; then fix_source_links; fi

if [ "$HLS_REQUIRES_PATCH" = true ]; then fix_source_game_links "hl1"; fi
if [ "$HL2_REQUIRES_PATCH" = true ]; then fix_source_game_links "hl2"; fi
if [ "$HL2LC_REQUIRES_PATCH" = true ]; then fix_source_game_links "lostcoast"; fi
if [ "$HL2EP_REQUIRES_PATCH" = true ]; then fix_source_game_links "episodic"; fi   

echo "Patching complete!"
show_success