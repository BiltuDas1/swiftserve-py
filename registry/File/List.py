from . import FileInfo


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
    if self.__list[filename] is not None:
      raise KeyError("The filename already exist")

    self.__list[filename] = fileinfo

  def remove(self, filename: str):
    if filename in self.__list:
      del self.__list[filename]
    else:
      raise KeyError(f"the filename `{filename}` doesn't exist")

  def get(self, filename: str):
    if filename in self.__list:
      return self.__list[filename]
    else:
      raise KeyError(f"the filename `{filename}` doesn't exist")

  def exist(self, filename: str):
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
