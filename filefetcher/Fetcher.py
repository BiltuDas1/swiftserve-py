import base64
import json
from blockchain.chain import Variables
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
    save_path = Env.get("FILE_DOWNLOADER_SAVE")
    with open(save_path, "ab") as f:
      f.write(Variables.START)
      f.write(base64.b64encode(json.dumps(job.to_dict()).encode('utf-8')))
      f.write(Variables.END)

  def get_work(self) -> Worker.FileWorker | None:
    """
    Getting the job from the worker list
    Returns:
      FileWorker: If the worker list is not empty
    """
    if len(self.__queue) == 0:
      return None

    # Remove the queue item from the hard disk
    save_path = Env.get("FILE_DOWNLOADER_SAVE")
    with open(save_path, "r+b") as f:
      f.seek(0)
      reading_pointer = 0
      writing_pointer = 0
      while True:
        data = f.read(1)
        if data.hex() == Variables.END.hex():
          reading_pointer = f.tell()
          break

      # Overwriting from the reading_pointer
      while len(data := f.read(1)) != 0:
        reading_pointer += 1
        f.seek(writing_pointer)
        f.write(data)
        writing_pointer += 1
        f.seek(reading_pointer)

    return self.__queue.popleft()

  def load(self, filepath: str):
    """
    Loads the Queue from the filepath
    Args:
      filepath: The path where the queue is saved
    """
    with open(filepath, "rb") as f:
      work: bytearray = bytearray()
      start = False
      while len(data := f.read(1)) != 0:
        if data.hex() == Variables.START.hex():
          start = True
        elif data.hex() == Variables.END.hex():
          start = False
          self.__queue.append(Worker.FileWorker.from_dict(
              json.loads(base64.b64decode(work).decode('utf-8'))))
          work.clear()
        else:
          if start:
            work.extend(data)

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

      not_next_chunk = False
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

          # If not downloaded the exact next chunk, then take the work and add it to the end of the work queue
          if not filelist.completed(work.filename, work.chunk):
            self.add_work(work)
            not_next_chunk = True
            break

          filelist_path = Env.get("FILELIST_PATH")
          filelist.save(filelist_path)
          # Appending the at the end of the file
          with open(destination_path, 'ab') as writeF:
            writeF.write(response.content)
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

      # If the current chunk is not next chunk, then skip task
      if not_next_chunk:
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
