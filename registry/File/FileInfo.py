from dataclasses import dataclass

@dataclass(frozen=True)
class FileInfo:
  """
  Class representing the details of a specific file, which required for synchronizing the file between nodes in the Blockchain
  """
  filehash: str
  size: int
  added_time: int
  total_chunks: int