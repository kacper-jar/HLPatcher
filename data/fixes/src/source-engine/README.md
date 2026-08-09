# 01_fixes.patch

Bug fixes allowing the source engine to successfully compile on macOS.

# 02_local_deps.patch

Adds local dependency build support via build_deps.py.

# 03_download_retry.patch

Adds download retry logic for unreliable connections when downloading dependencies.

# 04_openssl_fix.patch

Adds OpenSSL to the local dependency downloads in build_deps.py.
