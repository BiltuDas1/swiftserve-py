from dataclasses import dataclass


@dataclass(frozen=True)
class FileInfo:
  """
  Class representing the details of a specific file, which required for synchronizing the file between nodes in the Blockchain
  Args:
    filehash: The sha512 hash of the file
    size: The size of the file (In Bytes)
    added_time: The time when the file was added (Unix Time)
    total_chunks: The total chunks the file is seperated
  """

  filehash: str
  size: int
  added_time: int
  total_chunks: int

  def to_dict(self) -> dict:
    """
    Method converts the File object to Dictionary object
    """
    return {
        "filehash": self.filehash,
        "size": self.size,
        "added_time": self.added_time,
        "total_chunks": self.total_chunks,
    }

  @classmethod
  def from_dict(cls, data: dict) -> "FileInfo":
    """
    Method converts the Dictionary object to a File object
    """
    return cls(**data)
