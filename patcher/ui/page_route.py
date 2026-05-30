from enum import Enum


class PageRoute(Enum):
    WELCOME = "welcome"
    LIBRARY = "library"
    SELECTION = "selection"
    OPTIONS = "options"
    WARNING = "warning"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"
    NO_GAMES = "no_games"
    ALL_PATCHED = "all_patched"
    UPDATE_AVAILABLE = "update_available"

    # Interceptor specific routes
    SCAN_AND_ROUTE = "scan_and_route"
    CHECK_SOURCE_WARNING = "check_source_warning"
    HALT = "HALT"
