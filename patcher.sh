#!/bin/bash

VERSION="1.0.0"

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
    osascript <<EOF
        display dialog "Are you sure you want to patch your Half-Life installation?" buttons {"Cancel", "Patch"} default button "Patch" with icon caution
EOF
}

function show_sdl2_instructions() {
  # TODO: maybe replace this with auto download
    local folder="$1"
    osascript <<EOF
        display dialog "Before continuing, you need to install SDL2.\n\n1. Download SDL2 from:\nhttps://github.com/libsdl-org/SDL/releases/download/release-2.32.2/SDL2-2.32.2.dmg\n\n2. Open the DMG and drag SDL2.framework into the following folder:\n$folder/xash3d-fwgs/3rdparty\n\nOnce SDL2 is installed click OK" buttons {"OK"} default button "OK"
EOF
}

function show_success() {
    local folder="$1"
    osascript <<EOF
        display dialog "Patching complete! All files have been copied to:\n\n$folder" buttons {"OK"} default button 1 with icon note
EOF
}


show_welcome "$VERSION"

HL_FOLDER=$(choose_hl_folder)
if [[ "$HL_FOLDER" == "CANCELLED" ]]; then
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

confirm_patching
if [[ $? -ne 0 ]]; then
    exit 0
fi

show_sdl2_instructions "$SCRIPT_DIR"

echo "Patching Half-Life Engine..."
git clone --recursive https://github.com/FWGS/xash3d-fwgs "$SCRIPT_DIR/xash3d-fwgs" || exit 1
cd "$SCRIPT_DIR/xash3d-fwgs" || exit 1
./waf configure -8 --enable-bundled-deps --sdl2="$SCRIPT_DIR/xash3d-fwgs/3rdparty/SDL2.framework" build install --destdir="$SCRIPT_DIR/xash3d-fwgs/.output" || exit 1
cp -a "$SCRIPT_DIR/xash3d-fwgs/.output"/. "$HL_FOLDER" || exit 1
cp -a "$SCRIPT_DIR/xash3d-fwgs/3rdparty/SDL2.framework/" "$HL_FOLDER/SDL2.framework/" || exit 1
rm "$HL_FOLDER/hl_osx" || exit 1
mv "$HL_FOLDER/xash3d" "$HL_FOLDER/hl_osx" || exit 1

echo "Patching Half-Life..."
git clone --recursive https://github.com/FWGS/hlsdk-portable "$SCRIPT_DIR/hlsdk-portable-hlfixed" || exit 1
cd "$SCRIPT_DIR/hlsdk-portable-hlfixed" || exit 1
git checkout hlfixed || exit 1
./waf configure -T release -8 build install --destdir="$SCRIPT_DIR/hlsdk-portable-hlfixed/.output" || exit 1
cp -a "$SCRIPT_DIR/hlsdk-portable-hlfixed/.output"/. "$HL_FOLDER" || exit 1

echo "Patching complete!"
show_success "$HL_FOLDER"