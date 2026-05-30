from __future__ import annotations

SOURCE_LINK_FIXES = {
    "libvphysics.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libtogl.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libdatacache.dylib": [
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libvaudio_minimp3.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libmaterialsystem.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libvguimatsurface.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
        ("{thirdparty_prefix}/libfreetype.6.dylib", "@loader_path/libfreetype.6.dylib"),
        ("{thirdparty_prefix}/libfontconfig.1.dylib", "@loader_path/libfontconfig.1.dylib"),
        ("{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
    ],
    "libscenefilecache.dylib": [
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libsteam_api.dylib": [],
    "libServerBrowser.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
        ("{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
    ],
    "libinputsystem.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
        ("{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
        ("{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
    ],
    "libvideo_services.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libvgui2.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
        ("{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
    ],
    "libvtex_dll.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
        ("{thirdparty_prefix}/libjpeg.9.dylib", "@loader_path/libjpeg.9.dylib"),
        ("{thirdparty_prefix}/libpng16.16.dylib", "@loader_path/libpng16.16.dylib"),
        ("{thirdparty_prefix}/libz.1.dylib", "@loader_path/libz.1.3.1.dylib"),
    ],
    "libtier0.dylib": [],
    "libshaderapidx9.dylib": [
        ("{build_prefix}/togl/libtogl.dylib", "@loader_path/libtogl.dylib"),
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libGameUI.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
        ("{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
        ("{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
        ("{thirdparty_prefix}/libjpeg.9.dylib", "@loader_path/libjpeg.9.dylib"),
        ("{thirdparty_prefix}/libpng16.16.dylib", "@loader_path/libpng16.16.dylib"),
        ("{thirdparty_prefix}/libz.1.dylib", "@loader_path/libz.1.3.1.dylib"),
    ],
    "libstudiorender.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "liblauncher.dylib": [
        ("{build_prefix}/togl/libtogl.dylib", "@loader_path/libtogl.dylib"),
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
        ("{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
        ("{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
    ],
    "libfilesystem_stdio.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libstdshader_dx9.dylib": [
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libengine.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
        ("{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
        ("{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
        ("{thirdparty_prefix}/libjpeg.9.dylib", "@loader_path/libjpeg.9.dylib"),
        ("{thirdparty_prefix}/libz.1.dylib", "@loader_path/libz.1.3.1.dylib"),
        ("{thirdparty_prefix}/libcurl.4.dylib", "@loader_path/libcurl.4.dylib"),
    ],
    "libsoundemittersystem.dylib": [
        ("{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libpkgconf.7.dylib": [],
    "libpng16.16.dylib": [],
    "libfreetype.6.dylib": [
        ("{thirdparty_prefix}/libpng16.16.dylib", "@loader_path/libpng16.16.dylib"),
        ("{thirdparty_prefix}/libz.1.dylib", "@loader_path/libz.1.3.1.dylib"),
    ],
    "libz.1.3.1.dylib": [],
    "libjpeg.9.dylib": [],
    "libfontconfig.1.dylib": [
        ("{thirdparty_prefix}/libfreetype.6.dylib", "@loader_path/libfreetype.6.dylib"),
    ],
    "libcurl.4.dylib": [],
    "libedit.0.dylib": [],
    "libvstdlib.dylib": [
        ("{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
    ],
    "libopus.0.dylib": [],
}
