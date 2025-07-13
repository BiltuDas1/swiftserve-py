from django.urls import path
from . import views

urlpatterns = [
    path("addBlock", views.add_block),
    path("getHash", views.get_block_hash),
    path("topBlockNumber", views.get_top_block_number),
    path("totalBlocks", views.get_total_blocks_count),
    path("getBlockDatas", views.get_block_datas),
    path("key", views.get_public_key_of_node),
    path("overwriteBlockchain", views.overwrite_blockchain),
]
