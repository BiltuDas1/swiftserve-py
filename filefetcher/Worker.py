from dataclasses import dataclass


@dataclass(frozen=True)
class FileWorker:
  """
  Class refers to the Work of the downloading chunks
  """

  filename: str
  chunk: int
  total_chunks: int
  start_byte: int
  end_byte: int
  sha1: str
  ip_address: str
  port: int
