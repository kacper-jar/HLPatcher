#!/bin/bash

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

function prepare_common() {
    if [ "$CMAKE_NEEDED" = true ]; then
        echo "Preparing Python and CMake..."
        python3 -m venv "$WORKING_DIR/venv" || exit 1
        source "$WORKING_DIR/venv/bin/activate" || exit 1
        pip install cmake || exit 1
    fi
}

function prepare_hlsdk_mod() {
    local suffix="$1"
    local ref="$2"
    local dir_name="hlsdk-portable-${suffix}"
    
    echo "Preparing ${dir_name}..."
    git clone --recursive https://github.com/FWGS/hlsdk-portable "$WORKING_DIR/${dir_name}" || exit 1
    cd "$WORKING_DIR/${dir_name}" || exit 1
    git checkout "$ref" || exit 1
}

function prepare_goldsrc() {
    echo "Preparing GoldSrc Engine..."
    git clone --recursive https://github.com/FWGS/xash3d-fwgs "$WORKING_DIR/xash3d-fwgs" || exit 1
    curl -L -o "$WORKING_DIR/SDL2-2.32.8.dmg" "https://github.com/libsdl-org/SDL/releases/download/release-2.32.8/SDL2-2.32.8.dmg"
    SDL_MOUNT_POINT=$(hdiutil attach "$WORKING_DIR/SDL2-2.32.8.dmg" -nobrowse | grep -o '/Volumes/[^ ]*') || exit 1
    cp -a "$SDL_MOUNT_POINT/SDL2.framework/" "$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework/"
    hdiutil detach "$SDL_MOUNT_POINT"
}

function prepare_cstrike() {
    echo "Preparing Counter-Strike..."
    git clone --recursive https://github.com/Velaron/cs16-client.git "$WORKING_DIR/cs16-client" || exit 1
}

function build_hlsdk_mod() {
    local suffix="$1"
    local dir_name="hlsdk-portable-${suffix}"

    echo "Building ${dir_name}..."
    cd "$WORKING_DIR/${dir_name}" || exit 1
    ./waf configure -T release -8 build install --destdir="$WORKING_DIR/${dir_name}/output" || exit 1
}

function build_goldsrc() {
    echo "Building GoldSrc Engine..."
    cd "$WORKING_DIR/xash3d-fwgs" || exit 1
    ./waf configure -8 --enable-bundled-deps --sdl2="$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework" build install --destdir="$WORKING_DIR/xash3d-fwgs/output" || exit 1
}

function build_cstrike() {
    echo "Building Counter-Strike..."
    cd "$WORKING_DIR/cs16-client" || exit 1
    python3 -m cmake -S . -B build || exit 1
    python3 -m cmake --build build --config Release || exit 1
    python3 -m cmake --install build --prefix "$WORKING_DIR/cs16-client/output" || exit 1
}

function install_generic() {
    local dir_name="$1"
    echo "Installing ${dir_name}..."
    cp -a "$WORKING_DIR/${dir_name}/output"/. "$HL_FOLDER" || exit 1
}

function install_goldsrc() {
    echo "Installing GoldSrc Engine..."
    cp -a "$WORKING_DIR/xash3d-fwgs/output"/. "$HL_FOLDER" || exit 1
    cp -a "$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework/" "$HL_FOLDER/SDL2.framework/" || exit 1
    rm "$HL_FOLDER/hl_osx" || exit 1
    mv "$HL_FOLDER/xash3d" "$HL_FOLDER/hl_osx" || exit 1
}
