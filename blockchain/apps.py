from django.apps import AppConfig
from environments import Env
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from .chain import Key
import os
from .chain import Block, Blockchain
from .chain.ActionData import Node
from registry.Node.List import NodeList


class BlockchainConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "blockchain"

  def loadKey(self, filepath: str) -> Key.Key:
    """
    Loads the Key from the File system, if no key file found then generate a new one, and save it to the file path
    Args:
      filepath: The path of the private key
    Returns:
      Key: Returns the Key object containing the Private + Public Key
    """
    if not os.path.exists(filepath):
      prvkey = Ed25519PrivateKey.generate()
      ky = Key.Key(prvkey)
      ky.save_key(filepath)
    else:
      with open(filepath, "rb") as f:
        pem_data = f.read()

        # Trying to load private key
        prvkey = serialization.load_pem_private_key(
            pem_data, password=None)
        if not isinstance(prvkey, Ed25519PrivateKey):
          raise TypeError(
              "invalid private key, only Ed25519 keys are accepted"
          )

        ky = Key.Key(prvkey)

    return ky

  def ready(self) -> None:
    """
    Initialize the Application
    """
    downloads = str(Env.get("DOWNLOADS"))
    key_dir = os.path.join(downloads, "keys")
    os.makedirs(key_dir, exist_ok=True)
    key = self.loadKey(os.path.join(key_dir, "localkey.pem"))

    # If IP Address is not into Environment then set localhost IP as default
    currentNodeIP = os.getenv("MACHINE_IP", "127.0.0.1")

    # If Port number is not into Environment then make 8000 as default
    port = os.getenv("PORT", "8000")
    if not port.isnumeric():
      raise ValueError("PORT Environment variable can only be integers")

    port = int(port)
    if port >= 65536:
      raise ValueError("port number can't be more than 65535")
    if port <= 0:
      raise ValueError("port number can't be less than 1")

    Env.set("KEY", key)  # Loads the Private Key
    Env.set("IPADDRESS", currentNodeIP)
    Env.set("PORT", port)

    if (pubkey := key.get_private_key_raw()) is not None:
      genesis_block = Block.Block(
          0, "0", "add_node", Node.Node(
              currentNodeIP, port), currentNodeIP, port, pubkey
      )
    else:
      raise ValueError("no private key loaded")

    Env.set("CHAIN", Blockchain.Blockchain(genesis_block))

    chain_dir = os.path.join(downloads, "chaindata")
    os.makedirs(chain_dir, exist_ok=True)
    chain_file = os.path.join(chain_dir, "blockchain.bin")
    Env.set("CHAINDATA", chain_file)

    chain: Blockchain.Blockchain = Env.get("CHAIN")
    try:
      chain.load(chain_file)
    except FileNotFoundError:
      pass

    # Adding current node IP into the node list
    # nodelist: NodeList = Env.get("NODES")
    # nodelist.add(currentNodeIP, port)
