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
    Env.set("FILE_DOWNLOADER_SAVE", os.path.join(Env.get("DOWNLOADS"), "chaindata", "fetcher.bin"))
    Env.set("FILE_SENDER_SAVE", os.path.join(Env.get("DOWNLOADS"), "chaindata", "sender.bin"))

    file_downloader = Fetcher()
    if os.path.exists(Env.get("FILE_DOWNLOADER_SAVE")):
      file_downloader.load(Env.get("FILE_DOWNLOADER_SAVE"))
    Env.set("FILE_DOWNLOADER", file_downloader)

    file_sender = Sender()
    if os.path.exists(Env.get("FILE_SENDER_SAVE")):
      file_sender.load(Env.get("FILE_SENDER_SAVE"))
    Env.set("FILE_SENDER", Sender())

