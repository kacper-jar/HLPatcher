# HLPatcher
HLPatcher makes Half-Life playable on modern ARM Macs that only support 64-bit applications. It lets users to enjoy the game again without the hassle of manual binary update.

## Supported games
- Half-Life
- Half-Life: Opposing Force
- Half-Life: Blue Shift
- Deathmatch Classic

## Installation
1. Download the latest release from [GitHub Releases](https://github.com/kacper-jar/HLPatcher/releases) and unzip it.
2. Open the terminal and navigate to the unzipped directory.
3. Run the following command to install Xcode Command Line Tools:
```shell
xcode-select --install
```
> [!IMPORTANT]
> Xcode Command Line Tools are required for the patcher to build Xash3D FWGS binaries properly. You'll need to confirm the installation when prompted.
4. Start the patcher using this command:
```shell
chmod +x ./patcher.sh && ./patcher.sh
```

## Removing the Patches
If you need to remove the HLPatcher modifications and restore your original Half-Life installation, you have two options:

### Option 1: Restore from Backup (Recommended)
If you chose to create a backup during patching, you can easily restore your original installation:

1. Navigate to your Documents folder
2. Look for a folder named "Half-Life backup (YYYY-MM-DD)" with the date when you ran the patcher
3. Delete your current patched Half-Life installation folder
4. Copy the backup folder to replace your Half-Life installation
5. Rename the restored folder back to "Half-Life" (or whatever your original folder was named)

### Option 2: Verify Game Files through Steam
If you didn't create a backup or prefer using Steam's built-in verification:

1. Open Steam and go to your Library
2. Right-click on Half-Life (or the expansion you want to restore)
3. Select "Properties" from the context menu
4. Go to the "Local Files" tab
5. Click "Verify integrity of game files"
6. Steam will automatically download and restore any modified or missing files

> [!NOTE]
> Using Steam's file verification will restore all games in your Half-Life installation to their original state. If you only want to restore specific expansions, you may need to verify each game separately.

### Option 3: Complete Removal
For a complete clean installation:

1. Uninstall Half-Life through Steam
2. Manually delete the Half-Life installation folder to remove any leftover files
3. Reinstall Half-Life through Steam

This ensures all patched files and modifications are completely removed from your system.

## Thanks to
 - [Flying with Gauss](https://xash.su/) team for developing [Xash3D FWGS](https://github.com/FWGS/xash3d-fwgs) engine and [HLSDK Portable](https://github.com/FWGS/hlsdk-portable). Without them, HLPatcher wouldn't exist.

---

Made with ❤️ by [Kacper Jarosławski](https://github.com/kacper-jar)
