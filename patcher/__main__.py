import os
import certifi
import patcher
from patcher.app import App
from patcher.core import AppConfig, CommandExecutor, SessionLog

os.environ["SSL_CERT_FILE"] = certifi.where()

patcher.__version__ = os.environ.get("HLPATCHER_VERSION", "indev")

debug_mode = os.environ.get("HLPATCHER_DEBUG") == "1"
config = AppConfig(debug=debug_mode)

SessionLog.start(config.debug)

CommandExecutor.end_running_commands_on_exit()

app = App(config)
app.mainloop()
