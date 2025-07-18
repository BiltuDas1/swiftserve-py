from . import Worker
from threading import Thread
import httpx
import os
from environments import Env
import hashlib
from registry.File import List as FileList
from registry.Node import List as NodeList
from datetime import datetime
from collections import deque


class Fetcher:
  """
  Class refers to the download manager which will download chunks, in multi thread environment
  """

  def __init__(self):
    self.__queue: deque[Worker.FileWorker] = deque()
    self.__job = Thread(target=self.__work)

  def add_work(self, job: Worker.FileWorker):
    """
    Adding a new job to the worker list
    Args:
      job: The FileWorker object representing the job which needs to done
    """
    self.__queue.append(job)

  def __work(self):
    """
    Method refers to the job which will be done by the fetcher
    """
    while len(self.__queue) != 0:
      work = self.__queue.popleft()
      file_path: str = os.path.join(
          Env.get("DOWNLOADS"), f"{work.filename}.{work.chunk}.part"
      )

      # Fetching how much downloaded the current file
      downloaded = 0
      if os.path.exists(file_path):
        downloaded = os.path.getsize(file_path)

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

          if response.status_code in (200, 206):
            mode = "ab" if downloaded > 0 else "wb"
            with open(file_path, mode) as f:
              f.write(response.content)

          with open(file_path, "rb") as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()

          # If the file chunk is valid
          if sha1 == work.sha1:
            break
      else:
        print(f"invalid file chunk: {file_path}")
        destination_path: str = os.path.join(
            Env.get("DOWNLOADS"), work.filename
        )
        with open(Env.get("LOGFILE"), "a") as f:
          f.write(
              f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] failed to download `{work.filename}.{work.chunk}.part` of `{destination_path}`\n"
          )

        # Delete the incomplete chunk (If exist)
        if os.path.exists(file_path):
          os.remove(file_path)

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

      # If the chunk is the last part of the file then combine all the chunks to one file
      if work.chunk == work.total_chunks:
        destination_path: str = os.path.join(
            Env.get("DOWNLOADS"), work.filename
        )
        sha512 = hashlib.sha512()
        corrupted_chunks = False

        for chunk in range(1, work.chunk + 1):
          try:
            file_path: str = os.path.join(
                Env.get(
                    "DOWNLOADS"), f"{work.filename}.{chunk}.part"
            )
            with open(file_path, "rb") as f:
              data = f.read()
              sha512.update(data)

            with open(destination_path, "ab") as f:
              f.write(data)

            os.remove(file_path)  # Delete the chunk
          except OSError:
            corrupted_chunks = True
            break

        # Verifying the file hash
        if not corrupted_chunks:
          filelist: FileList.FileList = Env.get("FILES")
          fileinfo = filelist.get(work.filename)
          if sha512.hexdigest() != fileinfo.filehash:
            # Invalid File, so delete it
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
    Tells if the Fetcher is doing some jobs
    """
    return self.__job.is_alive()
