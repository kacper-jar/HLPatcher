#!/bin/bash

function show_no_cli_tools_error() {
  osascript <<EOF
      display dialog "Xcode Command Line Tools not found.\n\nPlease install them using 'xcode-select --install' command and relaunch HLPatcher." buttons {"OK"} default button 1 with icon caution
EOF
}

function show_welcome() {
  local version="$1"
  osascript <<EOF
      display dialog "Welcome to HLPatcher! ($version)\n\nThanks to:\n- Flying with Gauss team for developing Xash3D FWGS engine and HLSDK Portable.\n- Velaron for developing Counter-Strike 1.6 reverse-engineered client.\nWithout them, HLPatcher wouldn't exist.\n\nClick OK to continue." buttons {"OK"} default button 1
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

function choose_patch_mode() {
    osascript <<EOF
        set userChoice to button returned of (display dialog "Choose patching mode:\n\nLatest: Uses the most up-to-date code from source repositories. May contain new features but could be unstable.\n\nStable: Uses specific versions known to work well on macOS. Recommended if Latest fails." buttons {"Stable", "Latest"} default button "Latest" with icon note)
        return userChoice
EOF
}

function confirm_patching() {
    local patch_list=""
    local components_to_patch=0

    if [ "$GOLDSRC_REQUIRES_PATCH" = true ]; then
        patch_list+="GoldSrc Engine\n"
        ((components_to_patch++))
    fi

    if [ "$HL_REQUIRES_PATCH" = true ]; then
        patch_list+="Half-Life\n"
        ((components_to_patch++))
    fi

    if [ "$OPFOR_REQUIRES_PATCH" = true ]; then
        patch_list+="Half-Life: Opposing Force\n"
        ((components_to_patch++))
    fi

    if [ "$BSHIFT_REQUIRES_PATCH" = true ]; then
        patch_list+="Half-Life: Blue Shift\n"
        ((components_to_patch++))
    fi

    if [ "$DMC_REQUIRES_PATCH" = true ]; then
        patch_list+="Deathmatch Classic\n"
        ((components_to_patch++))
    fi

    if [ "$CSTRIKE_REQUIRES_PATCH" = true ]; then
        patch_list+="Counter-Strike\n"
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

function show_success() {
    osascript <<EOF
        display dialog "Patching complete!\n\nWarning!\nmacOS may block 'SDL2.framework' when launching the game for the first time. SDL2 is a crucial part of the game - it creates the game window and renders its content. Half-Life will not run without it.\n\nIf it gets blocked, open System Settings, go to 'Privacy & Security', and look for a message saying that SDL2.framework was blocked. Click the 'Open Anyway' button and confirm the action.\n\nEnjoy!" buttons {"OK"} default button 1
EOF
}
