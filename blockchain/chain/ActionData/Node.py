from dataclasses import dataclass
from . import ActionData

@dataclass(frozen=True)
class Node(ActionData):
  """
  Node record refers to the actionData which only applies to the actionTypes:
  'add_node', 'remove_node'
  """
  nodeIP: str

  def to_dict(self) -> dict:
    """
    Method converts the Node object to Dictionary object
    """
    return {
      'nodeIP': self.nodeIP,
    }

  @classmethod
  def from_dict(cls, data: dict) -> 'Node':
    """
    Method converts the Dictionary object to a Node object
    """
    return cls(**data)
