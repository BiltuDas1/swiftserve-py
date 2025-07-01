from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from environments import Env
from .chain import Blockchain, Key, Block
from .chain.ActionData import Node
from .chain.exceptions import InvalidNextBlock, InconsistentTimeline, InconsistentHash, InvalidSignature, InconsistentBlockchainException
from registry.Node.List import NodeList
import math
import random
import httpx

def collided_block(ip_address: str, port: int, chain: Blockchain.Blockchain) -> int:
  """
  Checks a remote node's blockchain and finds the first mismatch block index.

  Args:
    ip_address: Remote node IP.
    port: Remote node port.
    chain: The local blockchain.

  Returns:
    int: -1 if same, otherwise the first mismatched block index.

  Raises:
    InconsistentBlockchainException: If remote blockchain is inconsistent.
  """
  end_block = NodeList.get_last_block_number(ip_address, port)
  total_blocks = NodeList.get_total_block_count(ip_address, port)

  if (end_block + 1) < total_blocks:
      raise InconsistentBlockchainException("Remote blockchain is inconsistent")

  start = end_block - total_blocks
  low, high = start, end_block

  # Binary Search
  while low < high:
    mid = (high - low) // 2 + low
    remote_hash = NodeList.get_hash(ip_address, port, mid)
    local_hash = chain.get_block_hash(mid)

    if remote_hash == local_hash:
      low = mid + 1
    else:
      high = mid

  remote_hash = NodeList.get_hash(ip_address, port, low)
  local_hash = chain.get_block_hash(low)

  if remote_hash == local_hash:
    return -1
  else:
    return low

def send_block(ip_address: str, port: int, blk: Block.Block):
  """
  Send the Blockchain block to the specific IP Address
  """
  httpx.post(
    url=f"http://{ip_address}:{port}/addBlock", 
    headers={'Content-Type': 'application/octet-stream'}, 
    content=blk.to_bytes()
  )


# Create your views here.
def add_block(response: HttpRequest):
  """
  HTTP Handler for Adding a block into blockchain
  """
  if response.method != "POST":
    return HttpResponseNotAllowed(["POST"])
  
  try:
    blk = Block.Block.from_bytes(response.body)
  except ValueError as v:
    return HttpResponse(str(v), status=400)
  
  chain: Blockchain.Blockchain = Env.get("CHAIN")

  # Trying to add the block into the chain
  try:
    chain.add(blk)
  except (InvalidSignature.InvalidSignature, FileExistsError) as e:
    # Invalid signature
    return HttpResponse(str(e), status=403)
    
  except (InvalidNextBlock.InvalidNextBlock, InconsistentTimeline.InconsistentTimeline, InconsistentHash.InconsistentHash):
    # Trying to sync the blockchain with other peers
    nodelist: NodeList = Env.get("NODES")
    port: int = Env.get("PORT")
    ip_address: str = Env.get("IPADDRESS")

    most_common_hash_nodes = NodeList.most_matched_hash_nodes(
      nodelist.random_picks(
        int(math.sqrt(nodelist.size()))
      ), 
      port, 
      chain.last_block_number()
    )

    # If the current node ip is into the most common hash nodes then stop
    if most_common_hash_nodes.count(ip_address) != 0:
      return HttpResponse("The new block is invalid", status=409)
    
    # Pick a random node from the list and then copy the blockchain data
    if len(most_common_hash_nodes) == 0:
      return HttpResponse("Unable to find Most common hash among the network", status=500)
    
    for _ in range(5):
      try:
        choosed_node_ip = random.choice(most_common_hash_nodes)
        position_of_collision = collided_block(choosed_node_ip, port, chain)
        blocks_data = NodeList.get_blocks_data(choosed_node_ip, port, position_of_collision)
        chain.load_blocks_data(blocks_data, position_of_collision)
        break
      except Exception:
        continue
    else:
      return HttpResponse("Unable to copy blockchain data from other nodes", status=500)

    # Now retrying adding the new block to the blockchain
    try:
      chain.add(blk)

      # Do respective operation
      action_data = blk.to_blockdata().action_data
      match blk.to_blockdata().action_type:
        case "add_node":
          if isinstance(action_data, Node.Node):
            nodelist.add(action_data.nodeIP)
          else:
            raise TypeError('Invalid action_data')
        case "remove_node":
          if isinstance(action_data, Node.Node):
            nodelist.remove(action_data.nodeIP)
          else:
            raise TypeError('Invalid action_data')
      

      # Telling random 4 or less nodes about the new block
      if nodelist.size() > 4:
        nodes = nodelist.random_picks(4)
      else:
        nodes = nodelist.random_picks(nodelist.size())

      for nodeIP in nodes:
        send_block(nodeIP, port, blk)
      
    except Exception:
      return HttpResponse("The new block is invalid", status=409)

  finally:
    return HttpResponse("", status=200)

def get_block_hash(response: HttpRequest):
  """
  HTTP Handler for getting the block hash of specific position block
  """
  chain: Blockchain.Blockchain = Env.get("CHAIN")

  if (num := response.GET.get("num")) is not None:
    hashvalue = chain.get_block_hash(int(num))
  else:
    hashvalue = ""
  
  return HttpResponse(hashvalue, content_type="text/plain")

def get_top_block_number(response: HttpRequest):
  """
  HTTP Handler for getting the top block number into the blockchain
  """
  chain: Blockchain.Blockchain = Env.get("CHAIN")
  return HttpResponse(chain.last_block_number(), content_type="text/plain")

def get_total_blocks_count(response: HttpRequest):
  """
  HTTP Handler for getting the length of the blockchain (Total block count)
  """
  chain: Blockchain.Blockchain = Env.get("CHAIN")
  return HttpResponse(chain.size(), content_type="text/plain")

def get_block_datas(response: HttpRequest):
  """
  HTTP Handler for getting the block datas from the specific start position to the end of the blockchain
  """
  if response.method == "POST":
    chain: Blockchain.Blockchain = Env.get("CHAIN")
    if (num := response.POST.get("num")) is not None:
      blk_data = chain.get_blocks_data(int(num))
    else:
      blk_data = bytes()

    return HttpResponse(blk_data, content_type="application/octet-stream")
  else:
    return HttpResponseNotAllowed(["POST"])

def get_public_key_of_node(response: HttpResponse):
  """
  HTTP Handler for getting the public key of the current node
  """
  key: Key.Key = Env.get("KEY")
  if (pubkey := key.get_public_key()) is not None:
    pubkey_new = "-----BEGIN PUBLIC KEY-----\n" + pubkey + "\n-----END PUBLIC KEY-----"
  else:
    pubkey_new = ""

  return HttpResponse(pubkey_new, content_type="text/plain")