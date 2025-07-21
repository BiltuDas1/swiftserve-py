from django.apps import AppConfig
from environments import Env
import os
from .Fetcher import Fetcher
from .Sender import Sender


class FilefetcherConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "filefetcher"

  def ready(self) -> None:
    """
    Initialize the application
    """
    Env.set("LOGFILE", os.path.join("error.log"))
    Env.set("FILE_DOWNLOADER_SAVE", os.path.join(
        Env.get("DOWNLOADS"), "chaindata", "fetcher.queue"))
    Env.set("FILE_SENDER_SAVE", os.path.join(
        Env.get("DOWNLOADS"), "chaindata", "sender.queue"))

    file_downloader = Fetcher()
    Env.set("FILE_DOWNLOADER", file_downloader)

    file_sender = Sender()
    Env.set("FILE_SENDER", file_sender)

    # Start the threads
    try:
      file_downloader.start()
      file_sender.start()
    except IndexError:
      pass
