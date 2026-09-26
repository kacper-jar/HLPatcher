from patcher.core.models import Component, Game


class Planner:
    def __init__(self, games: list[Game]):
        self._components = {c.id: c for game in games for c in game.components}

    def find_missing_dependencies(self, selected: list[Component]) -> list[str]:
        selected_ids = {c.id for c in selected}

        missing = []
        for component in selected:
            for dependency_id in component.depends_on:
                dependency = self._components.get(dependency_id)
                if dependency is None or (dependency.needs_patch and dependency_id not in selected_ids):
                    missing.append(dependency_id)
        return list(dict.fromkeys(missing))
