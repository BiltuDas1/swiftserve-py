from django.http import JsonResponse, HttpRequest, HttpResponseNotAllowed, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from environments import Env
from .File import List as FileList, FileInfo
from .Node import List as NodeList
import os
import hashlib
import time
import httpx
from blockchain.chain import Block, Blockchain, Key
from blockchain.chain.ActionData import File
from blockchain.views import send_block


def tell_about_chunk(
    file_details: FileInfo.FileInfo,
    filename: str,
    ip: str,
    port: int,
    machine_ip: str,
    chunk_num: int,
    start_byte: int,
    end_byte: int,
):
  """
  Function which tells other nodes about the specific chunk
  Args:
    file_details: The FileInfo Object of the file
    filename: The name of the file
    ip: The IP Address of the remote node
    port: The port number of the remote node
    machine_ip: The ip address of the current node
    chunk_num: The number of the chunk
    start_byte: The starting byte location of the chunk
    end_byte: The ending byte location of the chunk
  """
  # Getting the sha1 hash of current chunk
  file_path: str = os.path.join(Env.get("DOWNLOADS"), filename)
  with open(file_path, "rb") as f:
    f.seek(start_byte)
    length = (end_byte - start_byte) + 1
    sha1hash = hashlib.sha1(f.read(length)).hexdigest()

  # Telling other nodes about the chunk
  try:
    httpx.post(
        url=f"http://{ip}:{port}/response",
        data={
            "filename": filename,
            "chunk": chunk_num,
            "total_chunks": file_details.total_chunks,
            "start_byte": start_byte,
            "end_byte": end_byte,
            "sha1": sha1hash,
            "ip_address": machine_ip,
            "port": port,
        },
    )
  except httpx.ReadTimeout:
    pass


def tell_other_nodes(
    filename: str, file_details: FileInfo.FileInfo, start_range: int, end_range: int
):
  """
  Function tells random 4 nodes about the specific chunk
  """
  nodelist: NodeList.NodeList = Env.get("NODES")
  chain: Blockchain.Blockchain = Env.get("CHAIN")
  machine_ip: str = Env.get("IPADDRESS")
  port: int = Env.get("PORT")
  keyring: Key.Key = Env.get("KEY")
  chain_path: str = Env.get("CHAINDATA")

  if nodelist.size() > 4:
    picked_nodes = nodelist.random_picks(4)
  else:
    picked_nodes = nodelist.random_picks(nodelist.size())

  if (private_key := keyring.get_private_key_raw()) is not None:
    blk = Block.Block(
        chain.size(),
        chain.last_block_hash(),
        "add_file",
        File.File(filename, file_details.filehash, file_details.size),
        machine_ip,
        port,
        private_key,
    )
  else:
    raise ValueError("no private key found")

  chain.add(blk)
  chain.save(chain_path)

  # Sending the blocks to the nodes
  # And telling them that the current node have downloadable chunks
  for nodeIP, portNum in picked_nodes:
    send_block(nodeIP, portNum, blk)
    tell_about_chunk(
        file_details, filename, nodeIP, port, machine_ip, 1, start_range, end_range
    )


# Create your views here.
@csrf_exempt
def upload(response: HttpRequest):
  """
  Function to handle uploading of files
  """
  if response.method != "POST":
    return HttpResponseNotAllowed(["POST"])

  if not response.FILES.get("file"):
    return JsonResponse({"status": False, "reason": "no file selected"}, status=400)

  uploaded_file = response.FILES["file"]

  filelist: FileList.FileList = Env.get("FILES")
  if filelist.exist(uploaded_file.name):
    return JsonResponse(
        {
            "status": False,
            "reason": "filename already exist, please choose another filename",
        },
        status=500,
    )

  sha512 = hashlib.sha512()
  save_path: str = os.path.join(Env.get("DOWNLOADS"), uploaded_file.name)
  with open(save_path, "wb") as f:
    for chunk in uploaded_file.chunks():
      f.write(chunk)
      sha512.update(chunk)

  total_chunks = uploaded_file.size // (4 * 1024 * 1024)
  if (uploaded_file.size % (4 * 1024 * 1024)) != 0:
    total_chunks += 1

  file_details = FileInfo.FileInfo(
      sha512.hexdigest(), uploaded_file.size, int(time.time()), total_chunks
  )
  filelist.add(uploaded_file.name, file_details, downloaded=True)
  filepath: str = Env.get("FILELIST_PATH")
  filelist.save(filepath)

  # Sending 4MiB chunk
  if uploaded_file.size > (4 * 1024 * 1024):
    tell_other_nodes(uploaded_file.name, file_details,
                     0, (4 * 1024 * 1024) - 1)
  else:
    tell_other_nodes(uploaded_file.name, file_details,
                     0, uploaded_file.size)

  return JsonResponse({"status": True})


@csrf_exempt
def download(response: HttpRequest):
  """
  Handle download file requests
  """
  if response.method != "GET":
    return HttpResponseNotAllowed(["GET"])

  if (filename := response.GET.get("file")) is None:
    return JsonResponse(
        {"status": False, "reason": "provide a file parameter"}, status=400
    )

  filelist: FileList.FileList = Env.get("FILES")
  if not filelist.exist(filename):
    return JsonResponse({"status": False, "reason": "file not found"}, status=404)

  # Reading any Range header (For supporting of resume download)
  file_path: str = os.path.join(Env.get("DOWNLOADS"), filename)
  file_size = os.path.getsize(file_path)
  if (range_header := response.headers.get("Range")) is not None:
    start, end = range_header.strip().split("=")[1].split("-")
    start = int(start)
    if end.isdigit():
      end = int(end)

    with open(file_path, "rb") as f:
      f.seek(start)
      if isinstance(end, int):
        length = (end - start) + 1
        data = f.read(length)
      else:
        data = f.read()
      final_response = HttpResponse(data, status=206)
      final_response["Content-Type"] = "application/octet-stream"
      final_response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
      final_response["Content-Disposition"] = f"attachment; filename=\"{filename}\""
      return final_response
  else:
    with open(file_path, "rb") as f:
      final_response = HttpResponse(f.read(), status=200)
      final_response["Content-Type"] = "application/octet-stream"
      final_response["Content-Disposition"] = f"attachment; filename=\"{filename}\""
      return final_response
