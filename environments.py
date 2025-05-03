# This file is used for storing variables which will be shared globally (Only inside the app)
from typing import Any

class Env:
  __items: dict[str, Any] = {}

  @classmethod
  def set(cls, name: str, value: Any) -> None:
    """
    Set environment name and their value
    Args:
      name: The name of the environment
      value: The value of the environment
    Raises:
      IndexError: when the key name already exist
    """
    if name not in cls.__items:
      cls.__items[name] = value
    else:
      raise IndexError(f"key name `{name}` already exist")

  @classmethod
  def get(cls, name: str) -> Any:
    """
    Get environment value which is stored
    Args:
      name: The name of the environment

    Returns:
      Any: Returns the object which is linked with the Environment

    Raises:
      KeyError: when there is no environment with that name
    """
    return cls.__items[name]
  
  @classmethod
  def update(cls, name: str, value: Any) -> None:
    """
    Updates the environment value
    Args:
      name: The name of the environment
      value: The value of the environment
    Raises:
      KeyError: when the environment name doesn't exist
    """
    if name in cls.__items:
      cls.__items[name] = value
    else:
      raise KeyError(f"environment `{name}` doesn't exist")