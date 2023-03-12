#!/usr/bin/python3
import sys
from base64 import b64decode
from argparse import ArgumentParser
import requests
from google.protobuf.json_format import MessageToJson

from define_pb2 import QueryRegionListHttpRsp

def chunked(size, source):
  for i in range(0, len(source), size):
    yield source[i:i+size]

def main(args):
  if not args.url:
    message = sys.stdin.read()
  else:
    response = requests.get(args.url)
    if response.status_code != 200 or response.content == b"500":
        print(f"[!] Failed to fetch response from dispatch server; {{status_code={response.status_code}, content={response.content}}}")
        return
    message = response.content

  curr = QueryRegionListHttpRsp()
  curr.ParseFromString(b64decode(message))

  print(MessageToJson(curr, preserving_proto_field_name=True))

if __name__ == '__main__':
  parser = ArgumentParser(description = "Fetches and parses QueryRegionListHttpRsp")
  parser.add_argument('url', type=str, nargs='?', help="URL to fetch response from; expects base64 content on stdin if absent")

  sys.exit(main(parser.parse_args()))
