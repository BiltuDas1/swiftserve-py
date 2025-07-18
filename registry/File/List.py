from . import FileInfo
import json
import base64


class FileList:
  """
  FileList keep the details of the files
  """

  def __init__(self):
    self.__list: dict[str, FileInfo.FileInfo] = {}

  def add(self, filename: str, fileinfo: FileInfo.FileInfo):
    """
    Adds the file and their information
    Args:
      filename: The name of the file
      fileinfo: The file information
    Raises:
      KeyError: If the filename already exist into the system
    """
    if filename in self.__list:
      raise KeyError("The filename already exist")

    self.__list[filename] = fileinfo

  def remove(self, filename: str):
    """
    Removes the file from the list
    Args:
      filename: The name of the file
    Raises:
      KeyError: If the filename doesn't exist
    """
    if filename in self.__list:
      del self.__list[filename]
    else:
      raise KeyError(f"the filename `{filename}` doesn't exist")

  def get(self, filename: str) -> FileInfo.FileInfo:
    """
    Get the file information using filename
    Args:
      filename: The name of the file
    Raises:
      KeyError: If the filename doesn't exist
    """
    if filename in self.__list:
      return self.__list[filename]
    else:
      raise KeyError(f"the filename `{filename}` doesn't exist")

  def exist(self, filename: str) -> bool:
    """
    Check if the filename exist into the list
    Args:
      filename: The name of the file

    Returns:
      bool: Returns True if filename exist, otherwise False
    """
    if filename in self.__list:
      return True
    else:
      return False

  def save(self, filepath: str):
    """
    Save the FileList to a file
    Args:
      filepath: The path where to save the data at
    """
    data = {}
    for filename, fileinfo in self.__list.items():
      data[filename] = fileinfo.to_dict()

    with open(filepath, 'wb') as f:
      f.write(base64.b64encode(json.dumps(data).encode('utf-8')))

  def load(self, filepath: str):
    """
    Load the FileList from a file
    Args:
      filepath: The path where the file is saved
    """
    with open(filepath, 'rb') as f:
      bdata = base64.b64decode(f.read())
      obj: dict[str, dict] = json.loads(bdata)
      for filename, fileinfo in obj.items():
        self.__list[filename] = FileInfo.FileInfo.from_dict(fileinfo)
