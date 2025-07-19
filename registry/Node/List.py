import base64
import json
import httpx
from typing import List, Dict
import random


class NodeList:
  """
  NodeList keeps the IP addresses of all the nodes in the blockchain.
  """

  def __init__(self):
    self._ip_list: List[str] = []
    self._ip_set: set[str] = set()
    self._ports: dict[str, int] = {}

  def add(self, ip_address: str, port: int) -> bool:
    """
    Adds a unique IP address to the list.

    Args:
      ip_address: The IP address to add.
      port: The port number to add.

    Returns:
      bool: True if added successfully, False if it already exists.
    """
    if ip_address in self._ip_set:
      return False
    self._ip_set.add(ip_address)
    self._ip_list.append(ip_address)
    self._ports[ip_address] = port
    return True

  def remove(self, ip_address: str) -> bool:
    """
    Removes an IP address from the list.

    Args:
      ip_address: The IP address to remove.

    Returns:
      bool: True if removed, False if not found.
    """
    if ip_address not in self._ip_set:
      return False
    self._ip_set.remove(ip_address)
    self._ip_list.remove(ip_address)
    del self._ports[ip_address]
    return True

  def random_picks(self, k: int) -> List[tuple[str, int]]:
    """
    Picks k random IP addresses from the list.

    Args:
      k: Number of IPs to pick.

    Returns:
      List[tuple[str, int]]: List of randomly picked IP addresses and their ports.

    Raises:
      ValueError: If k is larger than the list size.
    """
    if k > len(self._ip_list):
      raise ValueError("Sample size exceeds list size")
    random_lst = random.sample(self._ip_list, k)
    final: List[tuple[str, int]] = []
    for ip in random_lst:
      final.append((ip, self._ports[ip]))

    return final

  def exists(self, ip_address: str) -> bool:
    """
    Checks if the given IP Address exist into the list or not

    Args:
      ip_address: The IP Address to look for

    Returns:
      bool: Return True if exist, otherwise False
    """
    return ip_address in self._ip_set

  def size(self) -> int:
    """
    Returns the total number of nodes.

    Returns:
      int: Size of the node list.
    """
    return len(self._ip_list)

  def save(self, filepath: str):
    """
    Save the NodeList into a file
    Args:
      filepath: The path where to save the data at
    """
    with open(filepath, 'wb') as f:
      f.write(base64.b64encode(json.dumps(self._ports).encode('utf-8')))

  def load(self, filepath: str):
    """
    Load the NodeList from a file
    Args:
      filepath: The path where the file is saved
    """
    with open(filepath, 'rb') as f:
      bdata = base64.b64decode(f.read())
      self._ports: dict[str, int] = json.loads(bdata)

      for ipAddress in self._ports.keys():
        self._ip_set.add(ipAddress)
        self._ip_list.append(ipAddress)

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
    response = httpx.post(url, content=str(
        start_block_num), headers=headers)
    return response.content

  @staticmethod
  def most_matched_hash_nodes(
      nodes: List[tuple[str, int]], block_num: int
  ) -> List[tuple[str, int]]:
    """
    Checks all nodes for a specific block's hash and returns the list of nodes
    that share the most common hash value.

    Args:
      nodes: IP Address + ports of the nodes
      block_num: Block number to check.

    Returns:
      List[tuple[str, int]]: List of nodes with the most matched hash.
    """
    hash_map: Dict[str, List[tuple[str, int]]] = {}
    most_common_hash = ""
    highest_count = 0

    for ip, port in nodes:
      try:
        hash_val = NodeList.get_hash(ip, port, block_num)
        hash_map[hash_val].append((ip, port))
        if len(hash_map[hash_val]) > highest_count:
          most_common_hash = hash_val
          highest_count = len(hash_map[hash_val])
      except Exception:
        continue

    return hash_map.get(most_common_hash, [])
