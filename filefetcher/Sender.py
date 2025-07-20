import base64
import json
from blockchain.chain import Variables
from . import Worker
import os
import httpx
from threading import Thread, Lock
from environments import Env
import time
import hashlib


class Sender:
  """
  Class which is used for telling the clients that the chunk is ready to deliver
  """

  def __init__(self):
    self.__queue: set[Worker.FileWorker] = set()
    self.__job = Thread(target=self.__work)
    self.__lck = Lock()

  def add_work(self, job: Worker.FileWorker):
    """
    Adding a new job to the worker list
    Args:
      job: The FileWorker object representing the job which needs to done
    """
    with self.__lck:
      self.__queue.add(job)

  def get_work(self) -> Worker.FileWorker | None:
    """
    Getting the job from the worker list
    Returns:
      FileWorker: If the worker list is not empty
    """
    with self.__lck:
      if len(self.__queue) == 0:
        return None

      return self.__queue.pop()

  def load(self, filepath: str):
    """
    Loads the Queue from the filepath
    Args:
      filepath: The path where the queue is saved
    """
    with self.__lck:
      with open(filepath, "rb") as f:
        work: bytearray = bytearray()
        start = False
        while len(data := f.read(1)) != 0:
          if data.hex() == Variables.START.hex():
            start = True
          elif data.hex() == Variables.END.hex():
            start = False
            self.__queue.add(Worker.FileWorker.from_dict(
                json.loads(base64.b64decode(work).decode('utf-8'))))
            work.clear()
          else:
            if start:
              work.extend(data)

  def save(self, filepath: str):
    """
    Saves the Queue to the filepath
    Args:
      filepath: The path where the queue will be saved
    """
    with self.__lck:
      with open(filepath, "wb") as f:
        for work in self.__queue:
          f.write(Variables.START)
          f.write(base64.b64encode(json.dumps(work.to_dict()).encode('utf-8')))
          f.write(Variables.END)

  def __work(self):
    """
    Method refers to the job which will be done by the Sender
    """
    downloads: str = Env.get("DOWNLOADS")

    while (work := self.get_work()) is not None:
      next_chunk = work.chunk + 1
      if next_chunk > work.total_chunks:
        self.save(Env.get("FILE_SENDER_SAVE"))
        continue

      filepath = os.path.join(downloads, work.filename)
      if not os.path.exists(filepath):
        self.add_work(work)
        self.save(Env.get("FILE_SENDER_SAVE"))
        continue

      # Calculating the start byte and the end byte
      start_byte = work.end_byte + 1
      with open(filepath, "rb") as f:
        f.seek(start_byte)
        sha1 = hashlib.sha1(f.read(4194304)).hexdigest()
        if next_chunk == work.total_chunks:
          end_byte = f.tell()
        else:
          end_byte = f.tell() - 1

      # The file is not loaded completely (Or maybe in the saving state)
      if start_byte >= end_byte:
        self.add_work(work)
        self.save(Env.get("FILE_SENDER_SAVE"))
        continue

      # Telling the client that the chunk is available
      machine_ip: str = Env.get("IPADDRESS")
      port: int = Env.get("PORT")
      try:
        response = httpx.post(
            url=f"http://{work.ip_address}:{work.port}/response",
            data={
                "filename": work.filename,
                "chunk": next_chunk,
                "total_chunks": work.total_chunks,
                "start_byte": start_byte,
                "end_byte": end_byte,
                "sha1": sha1,
                "ip_address": machine_ip,
                "port": port,
            },
            timeout=10
        )
        if response.status_code != 200:
          self.add_work(work)
          self.save(Env.get("FILE_SENDER_SAVE"))
          continue
      except Exception:
        self.add_work(work)
        self.save(Env.get("FILE_SENDER_SAVE"))
        continue

      self.save(Env.get("FILE_SENDER_SAVE"))
      time.sleep(2)

  def start(self):
    """
    Starts the operation of the Sender
    Raises:
      ChildProcessError: If the Sender is already running
      IndexError: If the task queue is empty
    """
    if self.__job.is_alive():
      raise ChildProcessError("job is already started")
    elif len(self.__queue) == 0:
      raise IndexError("task queue is empty")

    try:
      self.__job.start()
    except RuntimeError:
      self.__job = Thread(target=self.__work)
      self.__job.start()

  def join(self, timeout: float | None = None):
    """
    Helps to bring the Worker Thread to foreground
    """
    self.__job.join(timeout)

  def is_running(self) -> bool:
    """
    Tells if the Sender is doing some jobs
    """
    return self.__job.is_alive()
