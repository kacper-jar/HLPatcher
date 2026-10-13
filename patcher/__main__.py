import os
import certifi
import patcher
from patcher.app import App
from patcher.core import AppConfig, CommandExecutor, SessionLog
from pathlib import Path

os.environ["SSL_CERT_FILE"] = certifi.where()

patcher.__version__ = os.environ.get("HLPATCHER_VERSION", "indev")

debug_mode = os.environ.get("HLPATCHER_DEBUG") == "1"
python_bin = os.environ.get("HLPATCHER_PYTHON_BIN")
config = AppConfig(debug=debug_mode, python_bin=Path(python_bin) if python_bin else None)

SessionLog.start(config.debug)

CommandExecutor.end_running_commands_on_exit()

app = App(config)
app.mainloop()
