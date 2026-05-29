from __future__ import annotations

from patcher.core import EngineType, Game, PatchMode, Patcher
from patcher.core.pipeline.fetchers import GitFetcher, GoldSrcEngineFetcher
from patcher.core.pipeline.builders import WafBuilder, CMakeBuilder
from patcher.core.pipeline.installers import GenericInstaller, GoldSrcEngineInstaller


class GoldSrcPatcher:
    def __init__(self, patcher: Patcher):
        self.patcher = patcher
        self.context = patcher._context

    def _get_ref(self, branch: str, stable_commit: str, force_stable: bool = False) -> str:
        if force_stable or self.context.patch_mode == PatchMode.STABLE:
            return stable_commit
        return branch

    def process(self, selected_games: list[Game]):
        goldsrc_games = [g for g in selected_games if g.engine_type == EngineType.GOLDSRC]
        if not goldsrc_games:
            return

        game = goldsrc_games[0]
        selected_components = [c for c in game.components if c.needs_patch]

        engine_comp = next((c for c in selected_components if c.subfolder == ""), None)
        if engine_comp:
            self.patcher._notify_component("GoldSrc Engine")

            fetcher = GoldSrcEngineFetcher(
                self.patcher, "xash3d-fwgs", "https://github.com/FWGS/xash3d-fwgs", "", engine_comp.stable_commit
            )
            fetcher.fetch()

            sdl_path = self.patcher._context.working_dir / "xash3d-fwgs" / "3rdparty" / "SDL2.framework"
            builder = WafBuilder(
                self.patcher, "xash3d-fwgs", ["-8", "--enable-bundled-deps", f"--sdl2={sdl_path}"]
            )
            builder.build()

            installer = GoldSrcEngineInstaller(self.patcher, "xash3d-fwgs")
            installer.install(game)

        hlsdk_mods = []
        for c in selected_components:
            if c.subfolder == "valve":
                hlsdk_mods.append(("hlfixed", self._get_ref("hlfixed", c.stable_commit), "Half-Life", c))
            elif c.subfolder == "gearbox":
                hlsdk_mods.append(
                    ("opforfixed", self._get_ref("opforfixed", c.stable_commit), "Half-Life: Opposing Force", c))
            elif c.subfolder == "bshift":
                hlsdk_mods.append(("bshift", self._get_ref("bshift", c.stable_commit), "Half-Life: Blue Shift", c))
            elif c.subfolder == "dmc":
                hlsdk_mods.append(
                    ("dmc", self._get_ref("dmc", c.stable_commit, force_stable=True), "Deathmatch Classic", c))

        for suffix, ref, mod_name, comp in hlsdk_mods:
            self.patcher._notify_component(mod_name)
            dir_name = f"hlsdk-portable-{suffix}"
            force_stable = (suffix == "dmc")

            fetcher = GitFetcher(
                self.patcher, dir_name, "https://github.com/FWGS/hlsdk-portable", ref, comp.stable_commit, force_stable
            )
            fetcher.fetch()

            builder = WafBuilder(self.patcher, dir_name, ["-T", "release", "-8"])
            builder.build()

            installer = GenericInstaller(self.patcher, dir_name)
            installer.install(game)

        cs_comp = next((c for c in selected_components if c.subfolder == "cstrike"), None)
        if cs_comp:
            self.patcher._notify_component("Counter-Strike")

            fetcher = GitFetcher(
                self.patcher, "cs16-client", "https://github.com/Velaron/cs16-client.git", "", cs_comp.stable_commit
            )
            fetcher.fetch()

            self.patcher._patch_generic("cs16-client")

            builder = CMakeBuilder(self.patcher, "cs16-client")
            builder.build()

            installer = GenericInstaller(self.patcher, "cs16-client")
            installer.install(game)
