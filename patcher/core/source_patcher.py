from __future__ import annotations

from patcher.core import EngineType, Game, Patcher
from patcher.core.pipeline.fetchers import GitFetcher
from patcher.core.pipeline.builders import WafBuilder
from patcher.core.pipeline.installers import SourceInstaller


class SourcePatcher:
    def __init__(self, patcher: Patcher):
        self.patcher = patcher
        self.context = patcher._context

    def process(self, selected_games: list[Game]):
        source_games = [g for g in selected_games if g.engine_type == EngineType.SOURCE]
        if not source_games:
            return

        waf_games = set()
        all_selected_comps = []
        for game in source_games:
            selected_comps = [c for c in game.components if c.needs_patch]
            if selected_comps:
                all_selected_comps.extend([(game, c) for c in selected_comps])
                for comp in selected_comps:
                    if comp.waf_game:
                        waf_games.add(comp.waf_game)

        if not all_selected_comps:
            return

        source_comp = all_selected_comps[0][1] if all_selected_comps else None

        self.patcher._notify_component("Source Engine")

        fetcher = GitFetcher(
            self.patcher, "source-engine", "https://github.com/nillerusr/source-engine", "", source_comp.stable_commit
        )
        fetcher.fetch()

        self.patcher._patch_generic("source-engine")

        waf_game_names = {
            "hl2": "Half-Life 2",
            "episodic": "Half-Life 2: Episodes",
            "hl1": "Half-Life: Source",
            "portal": "Portal",
        }

        for waf_game in waf_game_names:
            if waf_game in waf_games:
                game_title = waf_game_names[waf_game]
                self.patcher._notify_component(game_title)

                builder = WafBuilder(
                    self.patcher, "source-engine", ["-T", "release", "--prefix=", f"--build-games={waf_game}"]
                )
                builder.build()

        installer = SourceInstaller(self.patcher)
        for game in source_games:
            game_selected_comps = [c for g, c in all_selected_comps if g == game]
            if not game_selected_comps:
                continue

            subfolders = [c.subfolder for c in game_selected_comps]
            installer.install(game, subfolders=subfolders)
