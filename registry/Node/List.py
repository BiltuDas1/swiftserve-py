import httpx
from typing import List, Dict
import random
from collections import defaultdict


class NodeList:
  """
  NodeList keeps the IP addresses of all the nodes in the blockchain.
  """

  def __init__(self):
    self._list: List[str] = []
    self._set: set[str] = set()
    self._rand = random.Random()

  def add(self, ip_address: str) -> bool:
    """
    Adds a unique IP address to the list.

    Args:
      ip_address: The IP address to add.

    Returns:
      bool: True if added successfully, False if it already exists.
    """
    if ip_address in self._set:
      return False
    self._set.add(ip_address)
    self._list.append(ip_address)
    return True

  def remove(self, ip_address: str) -> bool:
    """
    Removes an IP address from the list.

    Args:
      ip_address: The IP address to remove.

    Returns:
      bool: True if removed, False if not found.
    """
    if ip_address not in self._set:
      return False
    self._set.remove(ip_address)
    self._list.remove(ip_address)
    return True

  def random_picks(self, k: int) -> List[str]:
    """
    Picks k random IP addresses from the list.

    Args:
      k: Number of IPs to pick.

    Returns:
      List[str]: List of randomly picked IP addresses.

    Raises:
      ValueError: If k is larger than the list size.
    """
    if k > len(self._list):
      raise ValueError("Sample size exceeds list size")
    return random.sample(self._list, k)

  def size(self) -> int:
    """
    Returns the total number of nodes.

    Returns:
      int: Size of the node list.
    """
    return len(self._list)

  @staticmethod
  def get_hash(ip_address: str, port: int, block_number: int) -> str:
    """
    Gets the hash of a specific block from a remote node.

    Args:
      ip_address: Target node IP.
      port: Port number.
      block_number: Block number.

    Returns:
      str: Hash of the block.
    """
    url = f"http://{ip_address}:{port}/getHash?num={block_number}"
    response = httpx.get(url)
    return response.text

  @staticmethod
  def get_last_block_number(ip_address: str, port: int) -> int:
    """
    Gets the top block number of a remote node.

    Args:
      ip_address: Target node IP.
      port: Port number.

    Returns:
      int: Last block number.
    """
    url = f"http://{ip_address}:{port}/topBlockNumber"
    response = httpx.get(url)
    return int(response.text)

  @staticmethod
  def get_total_block_count(ip_address: str, port: int) -> int:
    """
    Gets the total block count of a remote node.

    Args:
      ip_address: Target node IP.
      port: Port number.

    Returns:
      int: Total number of blocks.
    """
    url = f"http://{ip_address}:{port}/totalBlocks"
    response = httpx.get(url)
    return int(response.text)

  @staticmethod
  def get_blocks_data(ip_address: str, port: int, start_block_num: int) -> bytes:
    """
    Fetches all block data from a remote node starting from a specific block.

    Args:
      ip_address: Node IP.
      port: Port number.
      start_block_num: Start block number.

    Returns:
      bytes: Byte data of blocks.
    """
    url = f"http://{ip_address}:{port}/getBlockDatas"
    headers = {"Content-Type": "text/plain"}
    response = httpx.post(url, content=str(start_block_num), headers=headers)
    return response.content

  @staticmethod
  def most_matched_hash_nodes(nodes: List[str], port: int, block_num: int) -> List[str]:
    """
    Checks all nodes for a specific block's hash and returns the list of nodes
    that share the most common hash value.

    Args:
      nodes: IP addresses of nodes.
      port: Port number.
      block_num: Block number to check.

    Returns:
      List[str]: List of nodes with the most matched hash.
    """
    hash_map: Dict[str, List[str]] = {}
    most_common_hash = ""
    highest_count = 0

    for ip in nodes:
      try:
        hash_val = NodeList.get_hash(ip, port, block_num)
        hash_map[hash_val].append(ip)
        if len(hash_map[hash_val]) > highest_count:
          most_common_hash = hash_val
          highest_count = len(hash_map[hash_val])
      except Exception:
        continue

    return hash_map.get(most_common_hash, [])
