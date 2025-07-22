# SwiftServe

SwiftServe is a decentralized file-sharing service built with Python and Django. It leverages a private blockchain to securely manage node membership and track file availability across a peer-to-peer network, offering a file synchronization mechanism similar in concept to BitTorrent.

## Table of Contents

- [SwiftServe](#swiftserve)
  - [Table of Contents](#table-of-contents)
  - [How it works](#how-it-works)
  - [Environment Variables](#environment-variables)
  - [Installation](#installation)
    - [From Source](#from-source)
    - [Using Docker](#using-docker)
  - [How to run](#how-to-run)
  - [API Usage](#api-usage)
    - [GET Requests](#get-requests)
    - [POST Requests](#post-requests)

## How it works

- **Blockchain for State Management**: The service uses a private blockchain to maintain a distributed ledger of network nodes and file metadata. When a node joins or a file is added, a new block is created and propagated across the network. Each node independently validates and processes these blocks to maintain a consistent state.
- **Cryptographic Verification**: To ensure integrity and authenticity, each node cryptographically verifies new blocks. This includes checking the block's hash, the previous block's hash, and the creator's digital signature using the EdDSA algorithm.
- **Peer-to-Peer File Transfer Cycle**: File sharing is driven by a notification-based P2P cycle:
  1.  A node with a file chunk (the _sender_) notifies a random set of peers that the chunk is available.
  2.  A peer receiving the notification (the _downloader_) queues a task to download that chunk.
  3.  The downloader requests the chunk from the sender.
  4.  After downloading and verifying the chunk's SHA-1 hash, the downloader sends a confirmation back to the sender via a webhook.
  5.  This confirmation signals the sender to notify the downloader about the _next_ available chunk, continuing the cycle until the entire file is transferred.
- **Chunk-Based Downloads**: Files are transferred in 4MB chunks. Each chunk is verified with its SHA-1 hash upon receipt before being appended to the local file, ensuring data integrity throughout the transfer process.

## Environment Variables

| Name             | Description                                                                                                                                                                                  |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PORT`           | Tells in which port number the application will run, default value is 8000                                                                                                                   |
| `MACHINE_IP`     | It contains the environment which tells what is the IP Address of the current Machine (Must be accessible by the other nodes), default value is "127.0.0.1"                                  |
| `AUTO_DETECT_IP` | If this is set to 1, then the program will automatically find IP Address and then set it as `MACHINE_IP`, **Please Note: This environment only works when the program is running in docker** |

These variables should be set in your environment before running the application. For example, on Linux or macOS:

```bash
export PORT=8001
export MACHINE_IP=192.168.1.10
```

## Installation

### From Source

1. Clone this repo

```bash
git clone https://github.com/BiltuDas1/swiftserve-py
```

2. Now install all the dependencies using pip

```bash
pip install -r requirements.txt
```

3. [Start the server as described in the How to Run section.
   ](#how-to-run)

### Using Docker

1. Clone this repo

```bash
git clone https://github.com/BiltuDas1/swiftserve-py
```

2. Now build the docker image using

```bash
docker buildx -t swiftserve:latest .
```

## How to run

For starting the development server use

```bash
python manage.py runserver 0.0.0.0:8000
```

For starting the production server use

```bash
gunicorn swiftserve.wsgi:application --bind 0.0.0.0:8000
```

> **Note**: Using `0.0.0.0` binds the server to all available network interfaces, which is standard for production and containerized environments.

## API Usage

> **Note**: The links below point to the relevant implementation in the source code.

### GET Requests

- [`/getHash?num=<block_number>`](./blockchain/views.py#L191) - Retrieves the SHA256 hash of a specific block by its block number. Returns an empty string if the block does not exist.
- [`/topBlockNumber`](./blockchain/views.py#L206) - Returns the block number of the most recent block in the local blockchain.
- [`/totalBlocks`](./blockchain/views.py#L215) - Returns the total number of blocks in the local blockchain.
- [`/key`](./blockchain/views.py#L241) - Returns the Ed25519 public key of the current node in PEM format.
- [`/download?file=<name_of_the_file>`](./registry/views.py#L160) - Downloads a specified file. Supports `Range` headers for resuming downloads.

### POST Requests

- [`/addBlock`](./blockchain/views.py#L94) - Adds a new block to the blockchain. The request body must contain the serialized block data as `application/octet-stream`.
- [`/getBlockDatas`](./blockchain/views.py#L224) - Retrieves a serialized stream of block data starting from a specified block number (`num` field in the POST body).
- [`/overwriteBlockchain`](./blockchain/views.py#L257) - Replaces the local blockchain with the one provided in the request body. This is only permitted if the local chain contains just the genesis block, and is used for syncing new nodes.
- [`/upload`](./registry/views.py#L128) - Handles multipart file uploads. After storing the file, it creates an `add_file` block and notifies other peers.
- [`/response`](./filefetcher/views.py#L94) - Receives a notification from a peer that a specific file chunk is available for download. This triggers the local node to queue a download task for that chunk.
- [`/webhook`](./filefetcher/views.py#L135) - Receives a confirmation from a peer that a chunk has been successfully downloaded. This acts as a signal for the sender to offer the next available chunk to the downloader.
