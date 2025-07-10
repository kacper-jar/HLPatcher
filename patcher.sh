#!/bin/bash

VERSION="1.0.0"

WORKING_DIR="/tmp/HLPatcher"

HL_FOLDER=""

OPFOR_INSTALLED=false
BSHIFT_INSTALLED=false

function show_welcome() {
  local version="$1"
  osascript <<EOF
      display dialog "Welcome to HLPatcher! ($version)\n\nThanks to Flying with Gauss team for developing Xash3D FWGS engine and HLSDK Portable. Without them, HLPatcher wouldn't exist.\n\nClick OK to continue." buttons {"OK"} default button 1
EOF
}

function choose_hl_folder() {
    osascript <<EOF
        try
            set hlFolder to POSIX path of (choose folder with prompt "Select your Half-Life installation folder")
            return hlFolder
        on error
            return "CANCELLED"
        end try
EOF
}

function confirm_patching() {
    local patch_list="Half-Life"
    if [ "$OPFOR_INSTALLED" = true ]; then
        patch_list+="\nHalf-Life: Opposing Force"
    fi
    if [ "$BSHIFT_INSTALLED" = true ]; then
        patch_list+="\nHalf-Life: Blue Shift"
    fi
    osascript <<EOF
        display dialog "The following games will be patched:\n$patch_list\n\nIf your Half-Life installation becomes partially patched or corrupted, please uninstall the game via Steam, then delete the 'Half-Life' directory (the one you selected to patch) to remove any leftover files and try again.\n\nAre you sure you want to continue?" buttons {"Cancel", "Patch"} default button "Patch" with icon caution
EOF
}

function cleanup() {
    echo "Cleaning up..."
    if [ -d "$WORKING_DIR" ]; then
      rm -rf "$WORKING_DIR"
    fi
}

function show_success() {
    osascript <<EOF
        display dialog "Patching complete!\n\nWarning!\nmacOS may block 'SDL2.framework' when launching the game for the first time. SDL2 is a crucial part of the game - it creates the game window and renders its content. Half-Life will not run without it.\n\nIf it gets blocked, open System Settings, go to 'Privacy & Security', and look for a message saying that SDL2.framework was blocked. Click the 'Open Anyway' button and confirm the action.\n\nEnjoy!" buttons {"OK"} default button 1
EOF
}

trap cleanup EXIT INT TERM

show_welcome "$VERSION"

HL_FOLDER=$(choose_hl_folder)
if [[ "$HL_FOLDER" == "CANCELLED" ]]; then
    exit 0
fi

if [ -d "$HL_FOLDER/gearbox" ]; then
  echo "Opposing Force is installed."
  OPFOR_INSTALLED=true
fi

if [ -d "$HL_FOLDER/bshift" ]; then
  echo "Blue Shift is installed."
  BSHIFT_INSTALLED=true
fi

CONFIRM_PATCHING=$(confirm_patching)
if [[ "$CONFIRM_PATCHING" != *"button returned:Patch"* ]]; then
    exit 0
fi

if [ -d "$WORKING_DIR" ]; then
    rm -rf "$WORKING_DIR" || exit 1
fi
mkdir -p "$WORKING_DIR" || exit 1

echo "Patching Half-Life Engine..."
git clone --recursive https://github.com/FWGS/xash3d-fwgs "$WORKING_DIR/xash3d-fwgs" || exit 1
curl -L -o "$WORKING_DIR/SDL2-2.32.2.dmg" "https://github.com/libsdl-org/SDL/releases/download/release-2.32.2/SDL2-2.32.2.dmg"
SDL_MOUNT_POINT=$(hdiutil attach "$WORKING_DIR/SDL2-2.32.2.dmg" -nobrowse | grep -o '/Volumes/[^ ]*') || exit 1
cp -a "$SDL_MOUNT_POINT/SDL2.framework/" "$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework/"
hdiutil detach "$SDL_MOUNT_POINT"
cd "$WORKING_DIR/xash3d-fwgs" || exit 1
./waf configure -8 --enable-bundled-deps --sdl2="$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework" build install --destdir="$WORKING_DIR/xash3d-fwgs/.output" || exit 1
cp -a "$WORKING_DIR/xash3d-fwgs/.output"/. "$HL_FOLDER" || exit 1
cp -a "$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework/" "$HL_FOLDER/SDL2.framework/" || exit 1
rm "$HL_FOLDER/hl_osx" || exit 1
mv "$HL_FOLDER/xash3d" "$HL_FOLDER/hl_osx" || exit 1

echo "Patching Half-Life..."
git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-hlfixed" || exit 1
cd "$WORKING_DIR/hlsdk-portable-hlfixed" || exit 1
git checkout hlfixed || exit 1
./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-hlfixed/.output" || exit 1
cp -a "$WORKING_DIR/hlsdk-portable-hlfixed/.output"/. "$HL_FOLDER" || exit 1

if [ "$OPFOR_INSTALLED" = true ]; then
  echo "Patching Half-Life: Opposing Force..."
  git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-opforfixed" || exit 1
  cd "$WORKING_DIR/hlsdk-portable-opforfixed" || exit 1
  git checkout opforfixed || exit 1
  ./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-opforfixed/.output" || exit 1
  cp -a "$WORKING_DIR/hlsdk-portable-opforfixed/.output"/. "$HL_FOLDER" || exit 1
fi

if [ "$BSHIFT_INSTALLED" = true ]; then
  echo "Patching Half-Life: Blue Shift..."
  git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-bshift" || exit 1
  cd "$WORKING_DIR/hlsdk-portable-bshift" || exit 1
  git checkout bshift || exit 1
  ./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-bshift/.output" || exit 1
  cp -a "$WORKING_DIR/hlsdk-portable-bshift/.output"/. "$HL_FOLDER" || exit 1
fi

echo "Patching complete!"
show_success