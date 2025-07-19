from . import FileInfo
import json
import base64


class FileList:
  """
  FileList keep the details of the files
  """

  def __init__(self):
    self.__list: dict[str, tuple[FileInfo.FileInfo, int]] = {}

  def add(self, filename: str, fileinfo: FileInfo.FileInfo, downloaded=False):
    """
    Adds the file and their information
    Args:
      filename: The name of the file
      fileinfo: The file information
      downloaded: Set it True if the whole file is downloaded, otherwise False (Default False)
    Raises:
      KeyError: If the filename already exist into the system
    """
    if filename in self.__list:
      raise KeyError("The filename already exist")

    if downloaded:
      self.__list[filename] = (fileinfo, fileinfo.total_chunks)
    else:
      self.__list[filename] = (fileinfo, 0)

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
      return self.__list[filename][0]
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
      data[filename] = (fileinfo[0].to_dict(), fileinfo[1])

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
      obj: dict[str, tuple[dict, int]] = json.loads(bdata)
      for filename, fileinfo in obj.items():
        self.__list[filename] = (FileInfo.FileInfo.from_dict(fileinfo[0]), fileinfo[1])

  def completed(self, filename: str, chunk_num: int) -> bool:
    """
    Mark download complete of the specific chunk, make sure that you complete downloading the chunk serially, otherwise this method will throw an error
    Args:
      filename: The name of the file
      chunk_num: The chunk which download has been completed
    Returns:
      bool: Returns True if successful, otherwise False
    """
    fileinfo, cchunk = self.__list[filename]
    if (chunk_num == (cchunk + 1)) and (chunk_num <= fileinfo.total_chunks):
      self.__list[filename] = (fileinfo, chunk_num)
      return True
    else:
      return False

  def isDownloaded(self, filename: str) -> bool:
    """
    Check if the file is downloaded
    Args:
      filename: The name of the file
    Returns:
      bool: Returns True if downloaded, otherwise False
    """
    fileinfo, cchunk = self.__list[filename]
    return cchunk == fileinfo.total_chunks

  def getLastDownloadedChunk(self, filename: str) -> int:
    """
    Get the last downloaded chunk of the file
    Args:
      filename: The name of the file
    Returns:
      int: Returns the last downloaded chunk
    """
    return self.__list[filename][1]

  def size(self) -> int:
    """
    Get the size of the list
    Returns:
      int: Returns the size of the list
    """
    return len(self.__list)

  def getFiles(self) -> list[str]:
    """
    Get the list of files
    Returns:
      list[str]: Returns the list of files
    """
    return list(self.__list.keys())
