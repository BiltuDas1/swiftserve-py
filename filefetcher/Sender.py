import base64
import json

import persistqueue
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
    self.__queue: persistqueue.FIFOSQLiteQueue = persistqueue.FIFOSQLiteQueue(
        path=Env.get("FILE_SENDER_SAVE"), auto_commit=True, multithreading=True)
    self.__job = Thread(target=self.__work)

  def add_work(self, job: Worker.FileWorker):
    """
    Adding a new job to the worker list
    Args:
      job: The FileWorker object representing the job which needs to done
    """
    self.__queue.put(job)

  def get_work(self) -> Worker.FileWorker | None:
    """
    Getting the job from the worker list
    Returns:
      FileWorker: If the worker list is not empty
    """
    if self.__queue.empty():
      return None

    return self.__queue.get()

  def __work(self):
    """
    Method refers to the job which will be done by the Sender
    """
    downloads: str = Env.get("DOWNLOADS")

    while (work := self.get_work()) is not None:
      next_chunk = work.chunk + 1
      if next_chunk > work.total_chunks:
        continue

      filepath = os.path.join(downloads, work.filename)
      if not os.path.exists(filepath):
        self.add_work(work)
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
          continue
      except Exception:
        self.add_work(work)
        continue

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
    elif self.__queue.empty():
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
