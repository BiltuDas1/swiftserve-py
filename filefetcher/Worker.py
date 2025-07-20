from dataclasses import dataclass


@dataclass(frozen=True)
class FileWorker:
  """
  Class refers to the Work of the downloading chunks
  Args:
    filename: The name of the file
    chunk: The number of the chunk
    total_chunks: The count of total amount of chunks
    start_byte: The starting byte address of the chunk
    end_byte: The ending byte address of the chunk
    sha1: The sha1 hash of the chunk
    ip_address: IP Address of the sender of the chunk
    port: Port number of the sender
  """

  filename: str
  chunk: int
  total_chunks: int
  start_byte: int
  end_byte: int
  sha1: str
  ip_address: str
  port: int

  def to_dict(self) -> dict:
    """
    Method converts the FileWorker object to Dictionary object
    """
    return {
        "filename": self.filename,
        "chunk": self.chunk,
        "total_chunks": self.total_chunks,
        "start_byte": self.start_byte,
        "end_byte": self.end_byte,
        "sha1": self.sha1,
        "ip_address": self.ip_address,
        "port": self.port,
    }
  
  @classmethod
  def from_dict(cls, data: dict) -> "FileWorker":
    """
    Method converts the Dictionary object to a FileWorker object
    """
    return cls(**data)

