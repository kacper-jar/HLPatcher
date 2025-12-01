#!/bin/bash

STABLE_XASH3D_COMMIT="ab5ac3a"
STABLE_CS16_COMMIT="15278ca"
STABLE_HLFIXED_COMMIT="3c0044c"
STABLE_OPFORFIXED_COMMIT="a781ead"
STABLE_BSHIFT_COMMIT="8cffc25"
STABLE_DMC_COMMIT="895b28d"

STABLE_SOURCE_COMMIT="ed8209c"

function detect_patches() {
    if [[ "$ENGINE_TYPE" == "GoldSrc" ]]; then
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
            fi
        fi
    elif [[ "$ENGINE_TYPE" == "Source" ]]; then
        if [ -d "$HL_FOLDER/hl2" ]; then
            if [[ -f "$HL_FOLDER/hl2/bin/libclient.dylib" && -f "$HL_FOLDER/hl2/bin/libserver.dylib" ]]; then
                echo "Half-Life 2 - Already patched"
            else
                echo "Half-Life 2 - Needs patching"
                HL2_REQUIRES_PATCH=true
                SOURCE_REQUIRES_PATCH=true
            fi
        fi

        if [ -d "$HL_FOLDER/lostcoast" ]; then
            if [[ -f "$HL_FOLDER/lostcoast/bin/libclient.dylib" && -f "$HL_FOLDER/lostcoast/bin/libserver.dylib" ]]; then
                echo "Half-Life 2: Lost Coast - Already patched"
            else
                echo "Half-Life 2: Lost Coast - Needs patching"
                HL2LC_REQUIRES_PATCH=true
                SOURCE_REQUIRES_PATCH=true
            fi
        fi

        if [ -d "$HL_FOLDER/episodic" ]; then
            if [[ -f "$HL_FOLDER/episodic/bin/libclient.dylib" && -f "$HL_FOLDER/episodic/bin/libserver.dylib" ]]; then
                echo "Half-Life 2: Episode 1 & 2 - Already patched"
            else
                echo "Half-Life 2: Episode 1 & 2 - Needs patching"
                HL2EP_REQUIRES_PATCH=true
                SOURCE_REQUIRES_PATCH=true
            fi
        fi

        if [ -d "$HL_FOLDER/hl1" ]; then
            if [[ -f "$HL_FOLDER/hl1/bin/libclient.dylib" && -f "$HL_FOLDER/hl1/bin/libserver.dylib" ]]; then
                echo "Half-Life: Source - Already patched"
            else
                echo "Half-Life: Source - Needs patching"
                HLS_REQUIRES_PATCH=true
                SOURCE_REQUIRES_PATCH=true
            fi
        fi
        
        if [ "$SOURCE_REQUIRES_PATCH" = true ]; then
             echo "Source Engine - Needs patching"
        else
             echo "No supported Source engine games found or all are already patched."
        fi
    fi
}

function prepare_env() {
        echo "Preparing Python..."
        python3 -m venv "$WORKING_DIR/venv" || exit 1
        source "$WORKING_DIR/venv/bin/activate" || exit 1
        echo "Preparing build systems..."
        pip install cmake ninja meson || exit 1
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
    if [ "$PATCH_MODE" = "Stable" ] && [ -n "$STABLE_XASH3D_COMMIT" ]; then
        echo "Checking out stable commit: $STABLE_XASH3D_COMMIT"
        cd "$WORKING_DIR/xash3d-fwgs" || exit 1
        git checkout "$STABLE_XASH3D_COMMIT" || exit 1
        cd - > /dev/null
    fi
    curl -L -o "$WORKING_DIR/SDL2-2.32.8.dmg" "https://github.com/libsdl-org/SDL/releases/download/release-2.32.8/SDL2-2.32.8.dmg"
    SDL_MOUNT_POINT=$(hdiutil attach "$WORKING_DIR/SDL2-2.32.8.dmg" -nobrowse | grep -o '/Volumes/[^ ]*') || exit 1
    cp -a "$SDL_MOUNT_POINT/SDL2.framework/" "$WORKING_DIR/xash3d-fwgs/3rdparty/SDL2.framework/"
    hdiutil detach "$SDL_MOUNT_POINT"
}

function prepare_source() {
    echo "Preparing Source Engine..."
    git clone --recursive https://github.com/nillerusr/source-engine "$WORKING_DIR/source-engine" || exit 1
    if [ "$PATCH_MODE" = "Stable" ] && [ -n "$STABLE_SOURCE_COMMIT" ]; then
        echo "Checking out stable commit: $STABLE_SOURCE_COMMIT"
        cd "$WORKING_DIR/source-engine" || exit 1
        git checkout "$STABLE_SOURCE_COMMIT" || exit 1
        cd - > /dev/null
    fi
}

function prepare_cstrike() {
    echo "Preparing Counter-Strike..."
    git clone --recursive https://github.com/Velaron/cs16-client.git "$WORKING_DIR/cs16-client" || exit 1
    if [ "$PATCH_MODE" = "Stable" ] && [ -n "$STABLE_CS16_COMMIT" ]; then
        echo "Checking out stable commit: $STABLE_CS16_COMMIT"
        cd "$WORKING_DIR/cs16-client" || exit 1
        git checkout "$STABLE_CS16_COMMIT" || exit 1
        cd - > /dev/null
    fi
}

function patch_source() {
    echo "Patching Source Engine..."
    local patch_dir="$(cd "$(dirname "$0")/fixes/src/source-engine" && pwd)"
    
    if [ ! -d "$patch_dir" ]; then
        echo "Error: Patch directory $patch_dir not found."
        exit 1
    fi

    for patch_file in "$patch_dir"/*.patch; do
        if [ -f "$patch_file" ]; then
            echo "Applying patch: $(basename "$patch_file")"
            cd "$WORKING_DIR/source-engine" || exit 1
            patch -p1 < "$patch_file" || exit 1
        fi
    done
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

function build_source() {
    local game="$1"

    echo "Building $game..."
    cd "$WORKING_DIR/source-engine" || exit 1
    ./waf configure -T release --prefix='' --build-games="$game" build install --destdir="$WORKING_DIR/source-engine/output" || exit 1
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

function install_source_all() {
    echo "Installing Source Engine..."
    cp -a "$WORKING_DIR/source-engine/output"/ "$HL_FOLDER" || exit 1
    rm "$HL_FOLDER/hl2_osx" || exit 1
    mv "$HL_FOLDER/hl2_launcher" "$HL_FOLDER/hl2_osx" || exit 1
}

function install_lost_coast() {
    echo "Installing Lost Coast..."
    cp -a "$WORKING_DIR/source-engine/output/hl2/" "$HL_FOLDER/lostcoast/" || exit 1
}
