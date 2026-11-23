---
title: HLPatcher - Half-Life and Valve Games on Apple Silicon Macs
description: Free, open-source patcher that lets you play Half-Life, Half-Life 2, Portal, Counter-Strike and other Valve games natively on Apple Silicon Macs (M1, M2, M3, M4 and newer).
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

<div class="hero-shot" markdown>

![HLPatcher](imgs/index.png)

</div>

<div class="hero-text" markdown>

<div class="hero-brand">
<img src="imgs/icon.png" alt="" class="hero-logo">
<h1>HLPatcher</h1>
<p class="hero-subtitle">14 games, one patcher</p>
</div>

Free, open-source patcher that lets you play Half-Life, Half-Life 2, Portal, Counter-Strike and other Valve games natively on Apple Silicon Macs.

[Get Started](getting-started.md){ .md-button .md-button--primary } [Supported Games](supported-games.md){ .md-button .md-button--secondary }

<p class="download-count"></p>

</div>

</div>

<center markdown>

## Features

<div class="grid cards" markdown>

-   :material-controller:{ .lg .middle } **From Half-Life to Portal**

    Supports over 10 games, including GoldSrc and Source titles. See the [full list](supported-games.md).

-   :material-chip:{ .lg .middle } **Native on Apple Silicon**

    Your favourite Valve games run natively on Apple Silicon, without any translation layers (Rosetta).

-   :material-cog:{ .lg .middle } **Automated patching**

    Pick your games and HLPatcher downloads, builds and installs everything for you.

-   :material-steam:{ .lg .middle } **Your Steam games**

    Patches the copies you already own, and you keep launching them from Steam.

-   :material-map-marker-path:{ .lg .middle } **Guided steps**

    Shows a step-by-step guide when a game needs an older version.

-   :material-github:{ .lg .middle } **Free and open source**

    No cost, no account, and all the code is publicly available on GitHub.

</div>

## FAQ

<div class="grid cards card-list" markdown>

-   **Why won't Half-Life or Half-Life 2 run on my Mac?**

    Since macOS Catalina, Macs only run 64-bit apps. Valve never updated the Mac versions of these games, so they no longer start. HLPatcher builds 64-bit Apple Silicon versions and installs them into the games in your Steam library.

-   **Do I need Rosetta, Wine or a Windows copy of the game?**

    No. The patched games run natively on Apple Silicon, using the copies you already own on Steam.

-   **Which Macs are supported?**

    Apple Silicon Macs (M1 and newer). Intel Macs may work, but aren't officially supported.

-   **Do I need to install Xcode?**

    No, only the Xcode Command Line Tools, which are a much smaller download. [Getting Started](getting-started.md) shows how to install them.

-   **Why does HLPatcher ask me to switch to an older version of a game?**

    Some Source games only work with the patched engine on an older version of their game files. When a game needs it, HLPatcher shows a step-by-step guide for switching to that version in Steam.

-   **Can I play online?**

    Not on standard PC or VAC-secured servers. See each game's multiplayer limitations on the [Supported Games](supported-games.md) page.

-   **macOS says SDL2.framework can't be opened. What do I do?**

    This can happen the first time you launch a patched game. Open **System Settings**, go to **Privacy & Security** and click **Open Anyway**.

-   **Does a Steam update undo the patch?**

    It can, if the update replaces the game's binaries. If a patched game stops launching, reinstall it through Steam and run HLPatcher again.

-   **How do I undo the patch?**

    Restore your backup if you made one, verify the game files in Steam or reinstall the game. [Removing Patches](removing-patches.md) walks you through each option.

-   **Is HLPatcher free?**

    Yes. HLPatcher is free and [open source](https://github.com/kacper-jar/HLPatcher).

</div>

## Thanks to

<div class="grid cards card-list thanks-list" markdown>

-   **Flying with Gauss** for developing [Xash3D FWGS](https://github.com/FWGS/xash3d-fwgs) engine and [HLSDK Portable](https://github.com/FWGS/hlsdk-portable).

    [:fontawesome-solid-globe:](https://xash.su/){ title="Website" aria-label="Website" } [:octicons-mark-github-16:](https://github.com/FWGS){ title="GitHub" aria-label="GitHub" }

-   **Velaron** for developing [Counter-Strike 1.6 reverse-engineered client](https://github.com/Velaron/cs16-client).

    [:octicons-mark-github-16:](https://github.com/Velaron){ title="GitHub" aria-label="GitHub" }

-   **Nillerusr** for developing modifications in the [Source Engine](https://github.com/nillerusr/source-engine) repository.

    [:octicons-mark-github-16:](https://github.com/nillerusr){ title="GitHub" aria-label="GitHub" }

-   **Sethur (Tris)** for [fixing the mouse Y offset issue in fullscreen mode on devices with a camera notch](https://github.com/nillerusr/source-engine/pull/456).

    [:octicons-mark-github-16:](https://github.com/Sethur){ title="GitHub" aria-label="GitHub" }

</div>

Without them, HLPatcher wouldn't exist.

## Help Make HLPatcher Better

<div class="grid cards help-cards" markdown>

-   **Contribute**

    Help improve HLPatcher by contributing code or ideas.

    [Contributing Guide](contributing.md){ .md-button .md-button--primary }

-   **Translate**

    Make HLPatcher accessible in your native language.

    [:octicons-link-external-24: Crowdin](https://crowdin.com/project/hlpatcher){ .md-button .md-button--primary }

-   **Support Financially**

    If you enjoy HLPatcher, consider supporting the project.

    [:octicons-link-external-24: Buy Me a Coffee](https://buymeacoffee.com/kacperjar){ .md-button .md-button--primary }

</div>

## Copyright Notice

HLPatcher utilizes various third-party patches, modifications and open-source components to function. I respect the intellectual property rights of others.

If you are a copyright owner and believe that any material provided through this project infringes upon your rights, please submit a notification of your claim. You can contact me at [contact@hlpatcher.org](mailto:contact@hlpatcher.org) with the details and any infringing material will be promptly addressed.

---

### Made with ❤️ by Kacper Jarosławski

[:fontawesome-solid-globe: Website](https://kzl21.ovh/){ .md-button .md-button--secondary } [:octicons-mark-github-16: GitHub](https://github.com/kacper-jar){ .md-button .md-button--secondary }
</center>
