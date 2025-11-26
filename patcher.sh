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

if [[ "$(uname)" != "Darwin" ]]; then
    echo "This script can only be run on macOS."
    exit 1
fi

function detect_patches() {
    if [[ -f "$HL_FOLDER/libxash.dylib" && -d "$HL_FOLDER/SDL2.framework" && -f "$HL_FOLDER/libmenu.dylib" ]]; then
        echo "GoldSrc Engine - Already patched"
    else
        echo "GoldSrc Engine - Needs patching"
        GOLDSRC_REQUIRES_PATCH=true
    fi

    if [ -d "$HL_FOLDER/valve" ]; then
        if [[ -f "$HL_FOLDER/valve/dlls/hl.dylib" ]] && [[ -f "$HL_FOLDER/valve/cl_dlls/client.dylib" ]]; then
            if find "$HL_FOLDER/valve/dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q . || \
               find "$HL_FOLDER/valve/cl_dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q .; then
                echo "Half-Life - Already patched"
            else
                echo "Half-Life - Needs patching"
                HL_REQUIRES_PATCH=true
            fi
        else
            echo "valve folder exists but Half-Life game files not found."
        fi
    else
        echo "valve folder not found."
    fi

    if [ -d "$HL_FOLDER/gearbox" ]; then
        if find "$HL_FOLDER/gearbox/dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q . || \
           find "$HL_FOLDER/gearbox/cl_dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q .; then
            echo "Half-Life: Opposing Force - Already patched"
        else
            echo "Half-Life: Opposing Force - Needs patching"
            OPFOR_REQUIRES_PATCH=true
        fi
    fi

    if [ -d "$HL_FOLDER/bshift" ]; then
        if find "$HL_FOLDER/bshift/dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q . || \
           find "$HL_FOLDER/bshift/cl_dlls" -name "*_x86_64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q .; then
            echo "Half-Life: Blue Shift - Already patched"
        else
            echo "Half-Life: Blue Shift - Needs patching"
            BSHIFT_REQUIRES_PATCH=true
        fi
    fi

    if [ -d "$HL_FOLDER/dmc" ]; then
        if find "$HL_FOLDER/dmc/dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q . || \
           find "$HL_FOLDER/dmc/cl_dlls" -name "*_x86_64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q .; then
            echo "Deathmatch Classic - Already patched"
        else
            echo "Deathmatch Classic - Needs patching"
            DMC_REQUIRES_PATCH=true
        fi
    fi

    if [ -d "$HL_FOLDER/cstrike" ]; then
        if find "$HL_FOLDER/cstrike/dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q . || \
           find "$HL_FOLDER/cstrike/cl_dlls" -name "*_x86_64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q .; then
            echo "Counter-Strike - Already patched"
        else
            echo "Counter-Strike - Needs patching"
            CSTRIKE_REQUIRES_PATCH=true
            CMAKE_NEEDED=true
        fi
    fi
}

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
mkdir -p "$WORKING_DIR" || exit 1

if [ "$CMAKE_NEEDED" = true ]; then
  echo "Preparing Python and CMake..."
  python3 -m venv "$WORKING_DIR/venv" || exit 1
  source "$WORKING_DIR/venv/bin/activate" || exit 1
  pip install cmake || exit 1
fi

if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then
  echo "Patching Half-Life Engine..."
  git clone --recursive https://github.com/FWGS/xash3d-fwgs "$WORKING_DIR/xash3d-fwgs" || exit 1
  curl -L -o "$WORKING_DIR/SDL2-2.32.8.dmg" "https://github.com/libsdl-org/SDL/releases/download/release-2.32.8/SDL2-2.32.8.dmg"
  SDL_MOUNT_POINT=$(hdiutil attach "$WORKING_DIR/SDL2-2.32.8.dmg" -nobrowse | grep -o '/Volumes/[^ ]*') || exit 1
  cp -a "$SDL_MOUNT_POINT/SDL2.framework/" "$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework/"
  hdiutil detach "$SDL_MOUNT_POINT"
  cd "$WORKING_DIR/xash3d-fwgs" || exit 1
  ./waf configure -8 --enable-bundled-deps --sdl2="$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework" build install --destdir="$WORKING_DIR/xash3d-fwgs/.output" || exit 1
  cp -a "$WORKING_DIR/xash3d-fwgs/.output"/. "$HL_FOLDER" || exit 1
  cp -a "$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework/" "$HL_FOLDER/SDL2.framework/" || exit 1
  rm "$HL_FOLDER/hl_osx" || exit 1
  mv "$HL_FOLDER/xash3d" "$HL_FOLDER/hl_osx" || exit 1
fi

if [ "$HL_REQUIRES_PATCH" = true ]; then
  echo "Patching Half-Life..."
  git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-hlfixed" || exit 1
  cd "$WORKING_DIR/hlsdk-portable-hlfixed" || exit 1
  git checkout hlfixed || exit 1
  ./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-hlfixed/.output" || exit 1
  cp -a "$WORKING_DIR/hlsdk-portable-hlfixed/.output"/. "$HL_FOLDER" || exit 1
fi

if [ "$OPFOR_REQUIRES_PATCH" = true ]; then
  echo "Patching Half-Life: Opposing Force..."
  git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-opforfixed" || exit 1
  cd "$WORKING_DIR/hlsdk-portable-opforfixed" || exit 1
  git checkout opforfixed || exit 1
  ./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-opforfixed/.output" || exit 1
  cp -a "$WORKING_DIR/hlsdk-portable-opforfixed/.output"/. "$HL_FOLDER" || exit 1
fi

if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then
  echo "Patching Half-Life: Blue Shift..."
  git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-bshift" || exit 1
  cd "$WORKING_DIR/hlsdk-portable-bshift" || exit 1
  git checkout bshift || exit 1
  ./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-bshift/.output" || exit 1
  cp -a "$WORKING_DIR/hlsdk-portable-bshift/.output"/. "$HL_FOLDER" || exit 1
fi

if [ "$DMC_REQUIRES_PATCH" = true ]; then
  echo "Patching Deathmatch Classic..."
  git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-dmc" || exit 1
  cd "$WORKING_DIR/hlsdk-portable-dmc" || exit 1
  # Instead of checking out dmc branch, checkout one of previous commits on dmc branch.
  # Latest dmc branch commit is broken while adding this.
  git checkout 895b28d || exit 1
  ./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-dmc/.output" || exit 1
  cp -a "$WORKING_DIR/hlsdk-portable-dmc/.output"/. "$HL_FOLDER" || exit 1
fi

if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then
  echo "Patching Counter-Strike..."
  git clone --recursive https://github.com/Velaron/cs16-client.git "$WORKING_DIR/cs16-client" || exit 1
  cd "$WORKING_DIR/cs16-client" || exit 1
  python3 -m cmake -S . -B build || exit 1
  python3 -m cmake --build build --config Release || exit 1
  python3 -m cmake --install build --prefix "$WORKING_DIR/cs16-client/.output" || exit 1
  cp -a "$WORKING_DIR/cs16-client/.output"/. "$HL_FOLDER" || exit 1
fi

echo "Patching complete!"
show_success