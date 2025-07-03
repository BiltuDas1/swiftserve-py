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

    downloads = os.path.join('downloads')

    if not os.path.exists(downloads):
      os.mkdir(os.path.join('downloads'))
    Env.set("DOWNLOADS", os.path.join('downloads'))