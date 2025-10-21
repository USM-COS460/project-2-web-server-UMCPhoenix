## COS 460/540 - Computer Networks
# Project 2: HTTP Server

# <<Ian McLaughlin>>

This project is written in <<Python>> on <<Windows 11>>.

## How to compile

This project is written in Python3 and does not require a separate compilation step. It uses only the standard libaray modules. 
(socket, threading, sys, os, urllib.parse, and email.utils)

## How to run

The server is ran directly using the Python interpreter. It requires two command-line arguments; the port number to listen on and the document root.

    1. Ensure you have a document root directory with the files you want to serve. 
    2. Execute the script from your command line. (Powershell/CMD)

python http_server.py <port> <document_root>

## My experience with this project

Fill in here a brief summary of your experience with the project. What did you learn?

This project gave me a hands-on understanding of socket programming by building a TCP listener that manages the full client-server connection process. I designed the server with a multi-threaded structure using Python’s threading module so it could handle multiple client requests at once. One of the main things I learned was how to correctly follow the HTTP/1.1 protocol by manually creating the status line, adding key headers, and properly managing data in byte form.

I also gained useful security experience by adding path resolution logic that decodes URIs and prevents directory traversal attacks. This ensured that all requested files stayed within the server’s designated document root, keeping the system secure.
