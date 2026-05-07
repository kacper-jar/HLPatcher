import logging
import os
import patcher
from patcher.core import AppConfig

patcher.__version__ = os.environ.get("HLPATCHER_VERSION", "indev")

debug_mode = os.environ.get("HLPATCHER_DEBUG") == "1"
config = AppConfig(debug=debug_mode)

logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

app = patcher.App(config)
app.mainloop()
