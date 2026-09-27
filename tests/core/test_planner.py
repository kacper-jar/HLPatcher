import pytest

from patcher.core import EngineType, Game, PatchStatus, Planner


@pytest.fixture
def games(tmp_path, make_component):
    def comp(name, subfolder, engine_type, minutes, space_mb, **fields):
        return make_component(name, subfolder, engine_type, estimated_patch_time=minutes,
                              estimated_free_space_required=space_mb, **fields)

    goldsrc, source = EngineType.GOLDSRC, EngineType.SOURCE
    return [
        Game("Half-Life", tmp_path / "Half-Life", goldsrc, [
            comp("GoldSrc Engine", "", goldsrc, 1, 350, auto_select=True),
            comp("Half-Life", "valve", goldsrc, 1, 60, depends_on=["goldsrc-engine"]),
            comp("Opposing Force", "gearbox", goldsrc, 1, 60, depends_on=["goldsrc-engine"]),
        ]),
        Game("Half-Life 2", tmp_path / "Half-Life 2", source, [
            comp("Half-Life 2", "hl2", source, 3, 25),
            comp("Lost Coast", "lostcoast", source, 3, 25),
        ]),
        Game("Half-Life 2 Deathmatch", tmp_path / "Half-Life 2 Deathmatch", source, [
            comp("Half-Life 2: Deathmatch", "hl2mp", source, 3, 25, id="half-life-2-deathmatch",
                 depends_on=["half-life-2"]),
        ]),
        Game("Day of Defeat Source", tmp_path / "Day of Defeat Source", source, [
            comp("Day of Defeat: Source", "dod", source, 3, 25, id="day-of-defeat-source", depends_on=["half-life-2"]),
        ]),
    ]


@pytest.fixture
def components(games):
    return {comp.id: comp for game in games for comp in game.components}


@pytest.fixture
def select(components):
    return lambda *ids: [components[comp_id] for comp_id in ids]


@pytest.fixture
def planner(games, components):
    def make(patched=()):
        for comp_id in patched:
            components[comp_id].status = PatchStatus.ALREADY_PATCHED
        return Planner(games)

    return make


def summary(games):
    return [(game.name, [comp.id for comp in game.components]) for game in games]


def test_plans_the_selected_components_by_game_in_detection_order(planner, select):
    plan = planner().plan(select("half-life-2-deathmatch", "lost-coast", "half-life-2"))

    assert summary(plan) == [
        ("Half-Life 2", ["half-life-2", "lost-coast"]),
        ("Half-Life 2 Deathmatch", ["half-life-2-deathmatch"]),
    ]


def test_adds_the_auto_selected_engine_and_patches_it_first(games, planner, select):
    half_life = games[0]
    half_life.components.append(half_life.components.pop(0))

    plan = planner().plan(select("opposing-force", "half-life"))

    assert summary(plan) == [("Half-Life", ["goldsrc-engine", "half-life", "opposing-force"])]


def test_leaves_out_an_auto_selected_engine_that_is_already_patched(planner, select):
    plan = planner(patched=["goldsrc-engine"]).plan(select("half-life"))

    assert summary(plan) == [("Half-Life", ["half-life"])]


def test_does_not_add_dependencies_that_are_not_auto_selected(planner, select):
    plan = planner().plan(select("half-life-2-deathmatch"))

    assert summary(plan) == [("Half-Life 2 Deathmatch", ["half-life-2-deathmatch"])]


def test_plans_copies_of_the_games_and_leaves_the_originals_untouched(games, planner, select):
    half_life = games[0]

    [planned] = planner().plan(select("half-life"))

    assert (planned.name, planned.path, planned.engine_type) == (half_life.name, half_life.path, half_life.engine_type)
    assert [comp.id for comp in half_life.components] == ["goldsrc-engine", "half-life", "opposing-force"]


@pytest.mark.parametrize(("selected", "patched", "expected"), [
    ([], [], (0, 0)),
    (["half-life", "opposing-force"], [], (1 + 1 + 1, 350 + 60 + 60 + 150)),
    (["half-life"], ["goldsrc-engine"], (1, 60 + 150)),
    (["half-life-2", "lost-coast"], [], (3 + 3 + 9, 25 + 25 + 1500 + 150)),
    (["half-life", "half-life-2-deathmatch"], [], (1 + 1 + 3 + 9, 350 + 60 + 25 + 1500 + 150)),
], ids=["nothing", "mods-with-engine", "engine-already-patched", "source-games", "both-engines"])
def test_estimates_minutes_and_megabytes(planner, select, selected, patched, expected):
    assert planner(patched).estimate(select(*selected)) == expected


@pytest.mark.parametrize(("selected", "patched", "missing"), [
    (["half-life-2-deathmatch", "day-of-defeat-source"], [], ["half-life-2"]),
    (["half-life-2-deathmatch", "half-life-2"], [], []),
    (["half-life-2-deathmatch"], ["half-life-2"], []),
    (["half-life", "opposing-force"], [], []),
], ids=["not-selected", "selected-too", "already-patched", "auto-selected"])
def test_finds_dependencies_the_selection_leaves_unpatched(planner, select, selected, patched, missing):
    assert planner(patched).find_missing_dependencies(select(*selected)) == missing


def test_a_dependency_that_is_not_installed_is_missing(games, components):
    without_half_life_2 = [game for game in games if game.name != "Half-Life 2"]

    missing = Planner(without_half_life_2).find_missing_dependencies([components["half-life-2-deathmatch"]])

    assert missing == ["half-life-2"]
