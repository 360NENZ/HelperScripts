#!/usr/bin/python3
import sys
import json
from base64 import b64decode
from argparse import ArgumentParser

VECTOR_KEY = 0xA3

def main(args):
  if args.base64:
    payload = bytearray(b64decode(sys.stdin.read()))
  else:
    payload = bytearray.fromhex(sys.stdin.read())
  length = len(payload) - 1

  for i in range(length, -1, -1): # read from end
    if i == length:
      payload[i] ^= VECTOR_KEY
    else:
      payload[i] ^= payload[i + 1]

  try: 
    parsed = json.loads(payload)
    print(json.dumps(parsed, indent=4))
  except:
    print(payload.decode("utf-8"))

if __name__ == "__main__":
  parser = ArgumentParser(description="Decrypts and formats GameAnalyticsData", epilog="Data in selected format is read from stdin")
  parser.add_argument("--base64", action='store_true', help="Accept input as base64-encoded string (hex-string if not present)")

  sys.exit(main(parser.parse_args()))
