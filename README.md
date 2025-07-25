# HLPatcher
HLPatcher makes Half-Life playable on modern ARM Macs that only support 64-bit applications. It lets users to enjoy the game again without the hassle of manual binary update.

## Supported games
- Half-Life
- Half-Life: Opposing Force
- Half-Life: Blue Shift

## Installation
1. Download the latest release from [GitHub Releases](https://github.com/kacper-jar/HLPatcher/releases) and unzip it.
2. Open the terminal and navigate to the unzipped directory.
3. Install Xcode Command Line Tools by running:
```shell
xcode-select --install
```
> [!IMPORTANT]
> Xcode Command Line Tools are required for the patcher to build Xash3D FWGS binaries properly.
4. Make the patcher script executable:
```shell
chmod +x ./patcher.sh
```
> [!IMPORTANT]
> Skipping this step will prevent patcher from launching.
5. Run the patcher:
```shell
./patcher.sh
```

## Thanks to
 - [Flying with Gauss](https://xash.su/) team for developing [Xash3D FWGS](https://github.com/FWGS/xash3d-fwgs) engine and [HLSDK Portable](https://github.com/FWGS/hlsdk-portable). Without them, HLPatcher wouldn't exist.

---

Made with ❤️ by [Kacper Jarosławski](https://github.com/kacper-jar)
