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
    # If running in Docker container, then set the download path to /downloads, otherwise create a downloads directory into current path, and set it as download path
    dockerMode = bool(os.getenv("DOCKER", 0))
    if dockerMode:
      downloads = '/downloads'
    else:
      downloads = os.path.join("downloads")
      os.makedirs(downloads, exist_ok=True)

    Env.set("DOWNLOADS", downloads)

    chain_dir = os.path.join(downloads, "chaindata")

    # FileList
    filelist = os.path.join(chain_dir, 'filelist.bin')
    Env.set("FILELIST_PATH", filelist)

    fileListObj = FileList()
    if os.path.exists(filelist):
      fileListObj.load(filelist)

    Env.set("FILES", fileListObj)

    # NodeList
    nodelist = os.path.join(chain_dir, 'nodelist.bin')
    Env.set("NODELIST_PATH", nodelist)
    nodelistObj = NodeList()

    if os.path.exists(nodelist):
      nodelistObj.load(nodelist)
    Env.set("NODES", nodelistObj)
