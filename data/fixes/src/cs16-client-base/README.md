# 01_local_deps.patch

Adds local dependency build support via build_deps.py.

# 02_yapb_macos_build.patch

Lets YaPB inherit the macOS deployment target used by the CMake build and removes its explicit link against libstdc++.
