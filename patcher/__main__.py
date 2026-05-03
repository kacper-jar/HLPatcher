import logging
import os
import patcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

patcher.__version__ = os.environ.get("HLPATCHER_VERSION", "indev")

app = patcher.App()
app.mainloop()
