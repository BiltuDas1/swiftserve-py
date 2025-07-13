from django.apps import AppConfig
from environments import Env
from registry.Node.List import NodeList
from registry.File.List import FileList
import os


class RegistryConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "registry"

  def ready(self) -> None:
    """
    Initialize the Application
    """
    Env.set("NODES", NodeList())
    Env.set("FILES", FileList())

    # If running in Docker container, then set the download path to /downloads, otherwise create a downloads directory into current path, and set it as download path
    dockerMode = bool(os.getenv("DOCKER", 0))
    if dockerMode:
      downloads = '/downloads'
    else:
      downloads = os.path.join("downloads")
      os.makedirs(downloads, exist_ok=True)

    Env.set("DOWNLOADS", downloads)
