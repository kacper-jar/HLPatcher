from patcher.core.models import Component, EngineType, Game

SOURCE_ENGINE_BUILD_MINUTES = 9
SOURCE_ENGINE_BUILD_SPACE_MB = 1500
BUILD_TOOLS_SPACE_MB = 150


class Planner:
    def __init__(self, games: list[Game]):
        self._games = games
        self._components = {c.id: c for game in games for c in game.components}

    def plan(self, selected: list[Component]) -> list[Game]:
        planned_ids = self._planned_ids(selected)

        planned_games = []
        for game in self._games:
            components = sorted((c for c in game.components if c.id in planned_ids), key=lambda c: not c.auto_select)
            if components:
                planned_games.append(Game(name=game.name, path=game.path, engine_type=game.engine_type,
                                          components=components))
        return planned_games

    def estimate(self, selected: list[Component]) -> tuple[int, int]:
        planned = [c for game in self.plan(selected) for c in game.components]
        minutes = sum(c.estimated_patch_time for c in planned)
        space_mb = sum(c.estimated_free_space_required for c in planned)

        if any(c.engine_type == EngineType.SOURCE for c in planned):
            minutes += SOURCE_ENGINE_BUILD_MINUTES
            space_mb += SOURCE_ENGINE_BUILD_SPACE_MB
        if planned:
            space_mb += BUILD_TOOLS_SPACE_MB
        return minutes, space_mb

    def find_missing_dependencies(self, selected: list[Component]) -> list[str]:
        planned_ids = self._planned_ids(selected)

        missing = []
        for component in selected:
            for dependency_id in component.depends_on:
                dependency = self._components.get(dependency_id)
                if dependency is None or (dependency.needs_patch and dependency_id not in planned_ids):
                    missing.append(dependency_id)
        return list(dict.fromkeys(missing))

    def _planned_ids(self, selected: list[Component]) -> set[str]:
        planned_ids = {c.id for c in selected}
        for component in selected:
            for dependency_id in component.depends_on:
                dependency = self._components.get(dependency_id)
                if dependency is not None and dependency.auto_select and dependency.needs_patch:
                    planned_ids.add(dependency_id)
        return planned_ids
