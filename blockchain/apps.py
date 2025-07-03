from django.apps import AppConfig
from environments import Env
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from .chain import Key
import os
from .chain import Block, Blockchain
from .chain.ActionData import Node

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
          pem_data, password=None
        )
        if not isinstance(prvkey, Ed25519PrivateKey):
          raise TypeError("invalid private key, only Ed25519 keys are accepted")
      
        ky = Key.Key(prvkey)

    return ky

  def ready(self) -> None:
    """
    Initialize the Application
    """
    key = self.loadKey("localkey.pem")
    currentNodeIP = "127.0.0.1"
    port = 8000

    Env.set("KEY", key) # Loads the Private Key
    Env.set("IPADDRESS", currentNodeIP)
    Env.set("PORT", port)
    Env.set("SAVEPATH", os.getcwd() + "/downloads")

    if (pubkey := key.get_private_key_raw()) is not None:
      genesis_block = Block.Block(0, "0", "add_node", Node.Node(currentNodeIP), currentNodeIP, pubkey)
    else:
      raise ValueError("no private key loaded")

    Env.set("CHAIN", Blockchain.Blockchain(genesis_block))
