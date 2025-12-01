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
    cp -a "$WORKING_DIR/source-engine/thirdparty/install/lib/"*.dylib "$HL_FOLDER/bin/" || exit 1
    rm "$HL_FOLDER/hl2_osx" || exit 1
    mv "$HL_FOLDER/hl2_launcher" "$HL_FOLDER/hl2_osx" || exit 1
}

function install_lost_coast() {
    echo "Installing Lost Coast..."
    cp -a "$WORKING_DIR/source-engine/output/hl2/" "$HL_FOLDER/lostcoast/" || exit 1
}

function fix_source_links() {
    echo "Fixing Source Engine links..."
    cd "$HL_FOLDER/bin" || exit 1

    # libvphysics.dylib
    install_name_tool -id @loader_path/libvphysics.dylib libvphysics.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libvphysics.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libvphysics.dylib

    # libtogl.dylib
    install_name_tool -id @loader_path/libtogl.dylib libtogl.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libtogl.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libtogl.dylib

    # libdatacache.dylib
    install_name_tool -id @loader_path/libdatacache.dylib libdatacache.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libdatacache.dylib

    # libvaudio_minimp3.dylib
    install_name_tool -id @loader_path/libvaudio_minimp3.dylib libvaudio_minimp3.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libvaudio_minimp3.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libvaudio_minimp3.dylib

    # libmaterialsystem.dylib
    install_name_tool -id @loader_path/libmaterialsystem.dylib libmaterialsystem.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libmaterialsystem.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libmaterialsystem.dylib

    # libvguimatsurface.dylib
    install_name_tool -id @loader_path/libvguimatsurface.dylib libvguimatsurface.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libvguimatsurface.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libvguimatsurface.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libfreetype.6.dylib @loader_path/libfreetype.6.dylib libvguimatsurface.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libfontconfig.1.dylib @loader_path/libfontconfig.1.dylib libvguimatsurface.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libSDL2-2.0.0.dylib @loader_path/libSDL2-2.0.0.dylib libvguimatsurface.dylib

    # libscenefilecache.dylib
    install_name_tool -id @loader_path/libscenefilecache.dylib libscenefilecache.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libscenefilecache.dylib

    # libsteam_api.dylib
    install_name_tool -id @loader_path/libsteam_api.dylib libsteam_api.dylib

    # libServerBrowser.dylib
    install_name_tool -id @loader_path/libServerBrowser.dylib libServerBrowser.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libServerBrowser.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libServerBrowser.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/stub_steam/libsteam_api.dylib @loader_path/libsteam_api.dylib libServerBrowser.dylib

    # libinputsystem.dylib
    install_name_tool -id @loader_path/libinputsystem.dylib libinputsystem.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libinputsystem.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libinputsystem.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/stub_steam/libsteam_api.dylib @loader_path/libsteam_api.dylib libinputsystem.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libSDL2-2.0.0.dylib @loader_path/libSDL2-2.0.0.dylib libinputsystem.dylib

    # libvideo_services.dylib
    install_name_tool -id @loader_path/libvideo_services.dylib libvideo_services.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libvideo_services.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libvideo_services.dylib

    # libvgui2.dylib
    install_name_tool -id @loader_path/libvgui2.dylib libvgui2.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libvgui2.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libvgui2.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libSDL2-2.0.0.dylib @loader_path/libSDL2-2.0.0.dylib libvgui2.dylib

    # libvtex_dll.dylib
    install_name_tool -id @loader_path/libvtex_dll.dylib libvtex_dll.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libvtex_dll.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libvtex_dll.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libjpeg.9.dylib @loader_path/libjpeg.9.dylib libvtex_dll.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libpng16.16.dylib @loader_path/libpng16.16.dylib libvtex_dll.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libz.1.dylib @loader_path/libz.1.3.1.dylib libvtex_dll.dylib

    # libtier0.dylib
    install_name_tool -id @loader_path/libtier0.dylib libtier0.dylib

    # libshaderapidx9.dylib
    install_name_tool -id @loader_path/libshaderapidx9.dylib libshaderapidx9.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/togl/libtogl.dylib @loader_path/libtogl.dylib libshaderapidx9.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libshaderapidx9.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libshaderapidx9.dylib

    # libGameUI.dylib
    install_name_tool -id @loader_path/libGameUI.dylib libGameUI.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libGameUI.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libGameUI.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/stub_steam/libsteam_api.dylib @loader_path/libsteam_api.dylib libGameUI.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libSDL2-2.0.0.dylib @loader_path/libSDL2-2.0.0.dylib libGameUI.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libjpeg.9.dylib @loader_path/libjpeg.9.dylib libGameUI.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libpng16.16.dylib @loader_path/libpng16.16.dylib libGameUI.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libz.1.dylib @loader_path/libz.1.3.1.dylib libGameUI.dylib

    # libstudiorender.dylib
    install_name_tool -id @loader_path/libstudiorender.dylib libstudiorender.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libstudiorender.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libstudiorender.dylib

    # liblauncher.dylib
    install_name_tool -id @loader_path/liblauncher.dylib liblauncher.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/togl/libtogl.dylib @loader_path/libtogl.dylib liblauncher.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib liblauncher.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib liblauncher.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/stub_steam/libsteam_api.dylib @loader_path/libsteam_api.dylib liblauncher.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libSDL2-2.0.0.dylib @loader_path/libSDL2-2.0.0.dylib liblauncher.dylib

    # libfilesystem_stdio.dylib
    install_name_tool -id @loader_path/libfilesystem_stdio.dylib libfilesystem_stdio.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libfilesystem_stdio.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libfilesystem_stdio.dylib

    # libstdshader_dx9.dylib
    install_name_tool -id @loader_path/libstdshader_dx9.dylib libstdshader_dx9.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libstdshader_dx9.dylib

    # libengine.dylib
    install_name_tool -id @loader_path/libengine.dylib libengine.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libengine.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libengine.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/stub_steam/libsteam_api.dylib @loader_path/libsteam_api.dylib libengine.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libSDL2-2.0.0.dylib @loader_path/libSDL2-2.0.0.dylib libengine.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libjpeg.9.dylib @loader_path/libjpeg.9.dylib libengine.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libz.1.dylib @loader_path/libz.1.3.1.dylib libengine.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libcurl.4.dylib @loader_path/libcurl.4.dylib libengine.dylib

    # libsoundemittersystem.dylib
    install_name_tool -id @loader_path/libsoundemittersystem.dylib libsoundemittersystem.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libsoundemittersystem.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libsoundemittersystem.dylib

    # libshaderapidx9.dylib
    install_name_tool -id @loader_path/libshaderapidx9.dylib libshaderapidx9.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libshaderapidx9.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/libvstdlib.dylib libshaderapidx9.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/togl/libtogl.dylib @loader_path/libtogl.dylib libshaderapidx9.dylib

    # libpkgconf.7.dylib
    install_name_tool -id @loader_path/libpkgconf.7.dylib libpkgconf.7.dylib

    # libpng16.16.dylib
    install_name_tool -id @loader_path/libpng16.16.dylib libpng16.16.dylib

    # libfreetype.6.dylib
    install_name_tool -id @loader_path/libfreetype.6.dylib libfreetype.6.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libpng16.16.dylib @loader_path/libpng16.16.dylib libfreetype.6.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libz.1.dylib @loader_path/libz.1.3.1.dylib libfreetype.6.dylib

    # libz.1.3.1.dylib
    install_name_tool -id @loader_path/libz.1.3.1.dylib libz.1.3.1.dylib

    # libjpeg.9.dylib
    install_name_tool -id @loader_path/libjpeg.9.dylib libjpeg.9.dylib

    # libfontconfig.1.dylib
    install_name_tool -id @loader_path/libfontconfig.1.dylib libfontconfig.1.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libfreetype.6.dylib @loader_path/libfreetype.6.dylib libfontconfig.1.dylib

    # libcurl.4.dylib
    install_name_tool -id @loader_path/libcurl.4.dylib libcurl.4.dylib

    # libedit.0.dylib
    install_name_tool -id @loader_path/libedit.0.dylib libedit.0.dylib

    # libvstdlib.dylib
    install_name_tool -id @loader_path/libvstdlib.dylib libvstdlib.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/libtier0.dylib libvstdlib.dylib

    # libopus.0.dylib
    install_name_tool -id @loader_path/libopus.0.dylib libopus.0.dylib
}

function fix_source_game_links() {
    local game="$1"

    echo "Fixing source game links for $game..."
    cd "$HL_FOLDER/$game/bin"

    install_name_tool -id @loader_path/libclient.dylib libclient.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/../../bin/libvstdlib.dylib libclient.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/../../bin/libtier0.dylib libclient.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/stub_steam/libsteam_api.dylib @loader_path/../../bin/libsteam_api.dylib libclient.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/thirdparty/install/lib/libz.1.dylib @loader_path/../../lib/libz.1.3.1.dylib libclient.dylib

    install_name_tool -id @loader_path/libserver.dylib libserver.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/vstdlib/libvstdlib.dylib @loader_path/../../bin/libvstdlib.dylib libserver.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/tier0/libtier0.dylib @loader_path/../../bin/libtier0.dylib libserver.dylib
    install_name_tool -change /private/tmp/HLPatcher/source-engine/build/stub_steam/libsteam_api.dylib @loader_path/../../bin/libsteam_api.dylib libserver.dylib
}
