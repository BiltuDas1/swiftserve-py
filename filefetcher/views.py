from django.http import HttpRequest, HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import Fetcher, Worker
from environments import Env
import os

# Create your views here.
@csrf_exempt
def file_response_handler(response: HttpRequest):
  """
  This function watchs for if any node got any chunk of a specific file
  The json format would look like this:
  {
    "filename": "example.iso",
    "chunk": 1,
    "total_chunks": 1045,
    "start_byte": 0,
    "end_byte": 4194304,
    "sha1": <hash_of_the_chunk>,
    "ip_address: <ip_address_of_the_node_who_sended_the_response>,
    "port": 8000
  }
  """
  if response.method != "POST":
    return HttpResponseNotAllowed(["POST"])
  
  # Checking if the fileds are provided
  if (filename := response.POST.get("filename")) is None:
    return JsonResponse({'status': False, 'reason': 'provide `filename` field'}, status=400)
  
  if (chunk := response.POST.get("chunk")) is None:
    return JsonResponse({'status': False, 'reason': 'provide `chunk` field'}, status=400)
  
  if (total_chunks := response.POST.get("total_chunks")) is None:
    return JsonResponse({'status': False, 'reason': 'provide `total_chunks` field'}, status=400)
  
  if (start_byte := response.POST.get("start_byte")) is None:
    return JsonResponse({'status': False, 'reason': 'provide `start_byte` field'}, status=400)
  
  if (end_byte := response.POST.get("end_byte")) is None:
    return JsonResponse({'status': False, 'reason': 'provide `end_byte` field'}, status=400)
  
  if (sha1 := response.POST.get("sha1")) is None:
    return JsonResponse({'status': False, 'reason': 'provide `sha1` field'}, status=400)
  
  if (ip_address := response.POST.get("ip_address")) is None:
    return JsonResponse({'status': False, 'reason': 'provide `ip_address` field'}, status=400)
  
  if (port := response.POST.get("port")) is None:
    return JsonResponse({'status': False, 'reason': 'provide `port` field'}, status=400)
  
  # Checking if valid datatype
  if not chunk.isdigit():
    return JsonResponse({'status': False, 'reason': 'invalid `chunk` field'}, status=400)
  
  if not total_chunks.isdigit():
    return JsonResponse({'status': False, 'reason': 'invalid `total_chunks` field'}, status=400)
  
  if not start_byte.isdigit():
    return JsonResponse({'status': False, 'reason': 'invalid `start_byte` field'}, status=400)
  
  if not end_byte.isdigit():
    return JsonResponse({'status': False, 'reason': 'invalid `end_byte` field'}, status=400)
  
  if not port.isdigit():
    return JsonResponse({'status': False, 'reason': 'invalid `port` field'}, status=400)

  work = Worker.FileWorker(
    filename, int(chunk), int(total_chunks), int(start_byte), int(end_byte), sha1, ip_address, int(port)
  )

  # Check if the chunk is already downloaded by the node
  if os.path.exists(os.path.join(Env.get("DOWNLOADS"), f"{work.filename}.{chunk}.part")):
    return JsonResponse({'status': False, 'reason': f'chunk {work.chunk} is already downloaded'})

  # Add the download job into queue
  fetcher: Fetcher.Fetcher = Env.get("FILE_DOWNLOADER")
  fetcher.add_work(work)
  if not fetcher.is_running():
    fetcher.start()

  return JsonResponse({'status': True}, status=200)
