from dataclasses import dataclass
from . import ActionData


@dataclass(frozen=True)
class File(ActionData):
  """
  File record refers to the actionData which only applies to the actionTypes:
  'add_file', 'remove_file'
  Args:
    filename: The name of the file
    filehash: The sha512 hash of the file
    filesize: The size of the file (In Bytes)
  """

  filename: str
  filehash: str
  filesize: int

  def to_dict(self) -> dict:
    """
    Method converts the File object to Dictionary object
    """
    return {
        "filename": self.filename,
        "filehash": self.filehash,
        "filesize": self.filesize,
    }

  @classmethod
  def from_dict(cls, data: dict) -> "File":
    """
    Method converts the Dictionary object to a File object
    """
    return cls(**data)
