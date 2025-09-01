#!/bin/bash

VERSION="1.1.0"

WORKING_DIR="/tmp/HLPatcher"

HL_FOLDER=""

BACKUP_HL=false

OPFOR_INSTALLED=false
BSHIFT_INSTALLED=false

GOLDSRC_PATCHED=false
HL_PATCHED=false
OPFOR_PATCHED=false
BSHIFT_PATCHED=false

if [[ "$(uname)" != "Darwin" ]]; then
    echo "This script can only be run on macOS."
    exit 1
fi

function show_no_cli_tools_error() {
  osascript <<EOF
      display dialog "Xcode Command Line Tools not found.\n\nPlease install them using 'xcode-select --install' command and relaunch HLPatcher." buttons {"OK"} default button 1 with icon caution
EOF
}

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

function invalid_hl_folder() {
  osascript <<EOF
      display dialog "Half-Life executable not found!\n\nMake sure you selected the correct Half-Life installation directory. You have to select the folder inside which 'hl_osx' file is present." buttons {"OK"} default button 1 with icon caution
EOF
}

function backup_prompt() {
    osascript <<EOF
        set userChoice to button returned of (display dialog "Do you want to create a backup of your current Half-Life installation?\n\nIt will be stored inside your Documents folder." buttons {"No", "Yes"} default button "Yes" with icon caution)
        return userChoice
EOF
}

function confirm_patching() {
    local patch_list=""
    local components_to_patch=0

    if [ "$GOLDSRC_PATCHED" = false ]; then
        patch_list+="GoldSrc Engine\n"
        ((components_to_patch++))
    fi

    if [ "$HL_PATCHED" = false ]; then
        patch_list+="Half-Life\n"
        ((components_to_patch++))
    fi

    if [ "$OPFOR_INSTALLED" = true ] && [ "$OPFOR_PATCHED" = false ]; then
        patch_list+="Half-Life: Opposing Force\n"
        ((components_to_patch++))
    fi

    if [ "$BSHIFT_INSTALLED" = true ] && [ "$BSHIFT_PATCHED" = false ]; then
        patch_list+="Half-Life: Blue Shift\n"
        ((components_to_patch++))
    fi

    if [ $components_to_patch -eq 0 ]; then
        osascript <<EOF
            display dialog "All detected Half-Life components are already patched!\n\nNo patching is required." buttons {"OK"} default button 1 with icon note
EOF
        return 1
    fi

    osascript <<EOF
        set userChoice to button returned of (display dialog "The following components will be patched:\n$patch_list\nIf your Half-Life installation becomes partially patched or corrupted, please uninstall the game via Steam, then delete the 'Half-Life' directory (the one you selected to patch) to remove any leftover files and try again.\n\nAre you sure you want to continue?" buttons {"Cancel", "Patch"} default button "Patch" with icon caution)
        return userChoice
EOF
}

function detect_patches() {
    echo "Detecting patch status..."

    if [[ -f "$HL_FOLDER/libxash.dylib" && -d "$HL_FOLDER/SDL2.framework" && -f "$HL_FOLDER/libmenu.dylib" ]]; then
        GOLDSRC_PATCHED=true
        echo "GoldSrc Engine - Already patched"
    else
        echo "GoldSrc Engine - Needs patching"
    fi

    if find "$HL_FOLDER/valve/dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q . || \
       find "$HL_FOLDER/valve/cl_dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q .; then
        HL_PATCHED=true
        echo "Half-Life - Already patched"
    else
        echo "Half-Life - Needs patching"
    fi

    if [ "$OPFOR_INSTALLED" = true ]; then
        if find "$HL_FOLDER/gearbox/dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q . || \
           find "$HL_FOLDER/gearbox/cl_dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q .; then
            OPFOR_PATCHED=true
            echo "Half-Life: Opposing Force - Already patched"
        else
            echo "Half-Life: Opposing Force - Needs patching"
        fi
    fi

    if [ "$BSHIFT_INSTALLED" = true ]; then
        if find "$HL_FOLDER/bshift/dlls" -name "*_arm64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q . || \
           find "$HL_FOLDER/bshift/cl_dlls" -name "*_x86_64.dylib" -o -name "*_x86_64.dylib" 2>/dev/null | grep -q .; then
            BSHIFT_PATCHED=true
            echo "Half-Life: Blue Shift - Already patched"
        else
            echo "Half-Life: Blue Shift - Needs patching"
        fi
    fi
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

if [ -d "$HL_FOLDER/gearbox" ]; then
  echo "Opposing Force is installed."
  OPFOR_INSTALLED=true
fi

if [ -d "$HL_FOLDER/bshift" ]; then
  echo "Blue Shift is installed."
  BSHIFT_INSTALLED=true
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

if [ "$GOLDSRC_PATCHED" = false ]; then
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

if [ "$HL_PATCHED" = false ]; then
  echo "Patching Half-Life..."
  git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-hlfixed" || exit 1
  cd "$WORKING_DIR/hlsdk-portable-hlfixed" || exit 1
  git checkout hlfixed || exit 1
  ./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-hlfixed/.output" || exit 1
  cp -a "$WORKING_DIR/hlsdk-portable-hlfixed/.output"/. "$HL_FOLDER" || exit 1
fi

if [ "$OPFOR_INSTALLED" = true ] && [ "$OPFOR_PATCHED" = false ]; then
  echo "Patching Half-Life: Opposing Force..."
  git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-opforfixed" || exit 1
  cd "$WORKING_DIR/hlsdk-portable-opforfixed" || exit 1
  git checkout opforfixed || exit 1
  ./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-opforfixed/.output" || exit 1
  cp -a "$WORKING_DIR/hlsdk-portable-opforfixed/.output"/. "$HL_FOLDER" || exit 1
fi

if [ "$BSHIFT_INSTALLED" = true ] && [ "$BSHIFT_PATCHED" = false ]; then
  echo "Patching Half-Life: Blue Shift..."
  git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/hlsdk-portable-bshift" || exit 1
  cd "$WORKING_DIR/hlsdk-portable-bshift" || exit 1
  git checkout bshift || exit 1
  ./waf configure -T release -8 build install --destdir="$WORKING_DIR/hlsdk-portable-bshift/.output" || exit 1
  cp -a "$WORKING_DIR/hlsdk-portable-bshift/.output"/. "$HL_FOLDER" || exit 1
fi

echo "Patching complete!"
show_success