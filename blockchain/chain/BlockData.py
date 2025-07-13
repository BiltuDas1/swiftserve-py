from dataclasses import dataclass
import re
from .ActionData import ActionData, File, Node
from . import Variables


@dataclass(frozen=True)
class BlockData:
  """
  BlockData refers to the common block metadata,
  which exists in all blocks of the blockchain.
  """

  block_number: int
  previous_block_hash: str
  creation_time: int
  action_type: str
  action_data: ActionData
  creator_ip: str
  creator_port: int

  def __post_init__(self):
    if not re.fullmatch(r"^[0-9a-fA-F]+$", self.previous_block_hash):
      raise ValueError(
          "invalid previous_block_hash: not a valid hex string")

  def to_dict(self) -> dict:
    """
    Method converts the BlockData object to Dictionary object
    """
    return {
        "block_number": self.block_number,
        "previous_block_hash": self.previous_block_hash,
        "creation_time": self.creation_time,
        "action_type": self.action_type,
        "action_data": self.action_data.to_dict(),
        "creator_ip": self.creator_ip,
        "creator_port": self.creator_port
    }

  @classmethod
  def from_dict(cls, data: dict) -> "BlockData":
    """
    Method converts the Dictionary object to a BlockData object
    """
    if data["action_type"] in Variables.FileMethods:
      action_data = File.File.from_dict(data["action_data"])
    elif data["action_type"] in Variables.NodeMethods:
      action_data = Node.Node.from_dict(data["action_data"])
    else:
      raise TypeError("Invalid action_data")

    return cls(
        data["block_number"],
        data["previous_block_hash"],
        data["creation_time"],
        data["action_type"],
        action_data,
        data["creator_ip"],
        data["creator_port"]
    )
