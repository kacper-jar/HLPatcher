from enum import Enum


class PageRoute(Enum):
    WELCOME = "welcome"
    LIBRARY = "library"
    SELECTION = "selection"
    OPTIONS = "options"
    LIMITATIONS = "limitations"
    DOWNGRADE = "downgrade"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"
    NO_GAMES = "no_games"
    ALL_PATCHED = "all_patched"
    UPDATE_AVAILABLE = "update_available"

    # Interceptor specific routes
    SCAN_AND_ROUTE = "scan_and_route"
    CHECK_DOWNGRADE = "check_downgrade"
    HALT = "HALT"
