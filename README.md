# SwiftServe

This is the service which uses private blockchain to share files between nodes, we can use it for copying the files between multiple computers, like bittorrent.

## How it works

- It uses a blockchain to keep list of the nodes, file changes. Suppose if a block found which tells that a new node have joined into the network, then the block is shared with the each nodes and then the node which saw the block keep the final list into their local database.
- Each node verify the block information when they encounter, they verify the block hash, previous block hash, the signature of the node which created the block (Using EdDSA). And when everything looks Ok then it start following the operation of it.
- The system uses Webhook system to share files between nodes, The server tells random clients that it have a specific file, then the random clients start asking for the file information to the server, and this systems works continuously until all the nodes have the specific file.

## Environments

| Name         | Description                                                                                                                                                 |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PORT`       | Tells in which port number the application will run, default value is 8000                                                                                  |
| `MACHINE_IP` | It contains the environment which tells what is the IP Address of the current Machine (Must be accessible by the other nodes), default value is "127.0.0.1" |
|`AUTO_DETECT_IP`|If this is set to 1, then the program will automatically find IP Address and then set it as `MACHINE_IP`,  **Please Note: This environment only works when the program is running in docker** |
