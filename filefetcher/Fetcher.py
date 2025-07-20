import base64
import json
import time
from blockchain.chain import Variables
from . import Worker
from threading import Thread, Lock
import httpx
import os
from environments import Env
import hashlib
from registry.File import List as FileList
from registry.Node import List as NodeList
from datetime import datetime
from collections import deque
import persistqueue


class Fetcher:
  """
  Class refers to the download manager which will download chunks, in multi thread environment
  """

  def __init__(self):
    self.__queue: persistqueue.Queue = persistqueue.Queue(path=Env.get("FILE_DOWNLOADER_SAVE"), autosave=True)
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
    Method refers to the job which will be done by the fetcher
    """
    while (work := self.get_work()) is not None:
      destination_path: str = os.path.join(Env.get("DOWNLOADS"), work.filename)
      filelist: FileList.FileList = Env.get("FILES")

      # Check if the whole file is downloaded
      if filelist.isDownloaded(work.filename):
        continue

      # If not downloaded the exact next chunk, then take the work and add it to the end of the work queue
      if (filelist.getLastDownloadedChunk(work.filename) + 1) != work.chunk:
        self.add_work(work)
        continue

      # Downloading the file (If failed then retry 3 times)
      for _ in range(3):
        with httpx.Client() as client:
          try:
            response = client.get(
                url=f"http://{work.ip_address}:{work.port}/download",
                params={"file": work.filename},
                headers={
                    "Range": f"bytes={work.start_byte}-{work.end_byte}"},
            )
          except Exception:
            continue

          # If hash doesn't match, then retry downloading
          sha1 = hashlib.sha1(response.content).hexdigest()
          if sha1 != work.sha1:
            continue

          if response.status_code not in (200, 206):
            continue

          filelist_path = Env.get("FILELIST_PATH")
          filelist.save(filelist_path)
          # Appending the at the end of the file
          with open(destination_path, 'ab') as writeF:
            writeF.write(response.content)
          filelist.completed(work.filename, work.chunk)
          filelist.save(filelist_path)
          break
      else:
        print(f"invalid chunk {work.chunk}")
        destination_path: str = os.path.join(
            Env.get("DOWNLOADS"), work.filename
        )
        with open(Env.get("LOGFILE"), "a") as f:
          f.write(
              f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] failed to download chunk {work.chunk} of `{destination_path}`\n"
          )
        self.add_work(work)
        continue

      # Tell random 4 nodes about the new chunk
      port: int = Env.get("PORT")
      machine_ip: str = Env.get("IPADDRESS")
      nodelist: NodeList.NodeList = Env.get("NODES")
      if nodelist.size() > 4:
        nodes = nodelist.random_picks(4)
      else:
        nodes = nodelist.random_picks(nodelist.size())

      for ipAddress, portNum in nodes:
        try:
          httpx.post(
              url=f"http://{ipAddress}:{portNum}/response",
              data={
                  "filename": work.filename,
                  "chunk": work.chunk,
                  "total_chunks": work.total_chunks,
                  "start_byte": work.start_byte,
                  "end_byte": work.end_byte,
                  "sha1": work.sha1,
                  "ip_address": machine_ip,
                  "port": port,
              },
          )
        except Exception:
          continue

      # Tell the sender of the chunk that the current node have downloaded the chunk
      # So that the sender will tell the nodes when the other chunks will be available
      try:
        httpx.post(
            url=f"http://{work.ip_address}:{work.port}/webhook",
            data={
                "filename": work.filename,
                "chunk": work.chunk,
                "total_chunks": work.total_chunks,
                "start_byte": work.start_byte,
                "end_byte": work.end_byte,
                "sha1": work.sha1,
                "ip_address": machine_ip,
                "port": port,
            },
        )
      except Exception:
        pass

      # If the chunk is the last part of the file then check if the whole file is intact
      if work.chunk == work.total_chunks:
        with open(destination_path, 'rb') as f:
          sha512 = hashlib.sha512(f.read()).hexdigest()
          fileinfo = filelist.get(work.filename)
          if sha512 != fileinfo.filehash:
            # Invalid File, so delete it
            if os.path.exists(destination_path):
              os.remove(destination_path)

  def start(self):
    """
    Starts the operation of the Fetcher
    Raises:
      ChildProcessError: If the Fetcher is already running
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
    Tells if the Fetcher is doing some jobs
    """
    return self.__job.is_alive()
