import abc


class ActionData(abc.ABC):
  """
  Interface for ActionData-related types.
  Acts as a base class for serializable action data in blocks.
  """

  def to_dict(self) -> dict:
    """
    Method allows to convert ActionData type to Dictionary Object
    """
    return {}

  @classmethod
  @abc.abstractmethod
  def from_dict(cls, data: dict) -> "ActionData":
    """
    Method allows to convert Dictionary Object to ActionData type
    """
