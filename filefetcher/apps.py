from django.apps import AppConfig
from environments import Env
import os
from .Fetcher import Fetcher

class FilefetcherConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "filefetcher"

  def ready(self) -> None:
    """
    Initialize the application
    """
    Env.set("LOGFILE", os.path.join('error.log'))
    Env.set("FILE_DOWNLOADER", Fetcher())