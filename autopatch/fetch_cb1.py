#!/usr/bin/python3
import sys
import os
import requests
import logging
import signal
from shutil import copyfileobj
from posixpath import join as urljoin
from argparse import ArgumentParser

BASE_URL = "https://autopatchcn.yuanshen.com"

CLIENTS = [
  "StandaloneWindows64",
  "iOS"
]

RES_BASE_PATH = "client_game_res"
RES_FILES = [
  "AssetBundles/bundle_versions",
  "AssetBundles/svc_catalog",
  "AssetBundles/asset_index",
  "AssetBundles/zipMeta",
  "VideoAssets/video_versions",
  "AudioAssets/audio_versions"
]
RES_PARSEABLE_FILES = [
  "AssetBundles/zipMeta",
  "VideoAssets/video_versions",
  "AudioAssets/audio_versions"
]

CLIENT_BASE_PATH = "client_design_data"
CLIENT_FILES = [
  "AssetBundles/data_versions"
]

DIR_MAPPINGS = {
  ".zip": "AssetBundles",
  ".pck": "AudioAssets",
  ".mp4": "VideoAssets",
  ".srt": "VideoAssets"
}

def logger():
  return logging.getLogger(os.path.basename(__file__))

def sigint_handler(signal, frame):
  logger().info("Interrupted but nothing to clean up yet; exiting cleanly")
  sys.exit(130)

def fetch_file(rel_path, base_url, dst_dir):
  if os.path.exists(f"{dst_dir}/{rel_path}"):
    logger().debug(f"File {rel_path} already exists; skipping")
    return

  logger().info(f"Fetching {rel_path}...")
  try:
    response = requests.get(f"{base_url}/{rel_path}", stream=True)
  except Exception as err:
    logger().error(f"Failed to fetch {rel_path}; {err=}")
    return

  if response.status_code != 200:
    logger().error(f"Failed to fetch {rel_path}; status_code={response.status_code}")
    return

  os.makedirs(os.path.dirname(f"{dst_dir}/{rel_path}"), exist_ok=True) # need to create directory

  try:
    signal.signal(signal.SIGINT, signal.default_int_handler) # reset handler so we can catch exception
    with open(f"{dst_dir}/{rel_path}", "wb") as file:
      copyfileobj(response.raw, file, length=16*1024*1024) # write in 16M chunks
  except KeyboardInterrupt:
    logger().warning("Catched KeyboardInterrupt during download process; cleaning up partial files...")
    os.remove(f"{dst_dir}/{rel_path}")
    logger().info("Exiting cleanly")
    sys.exit(130)

  signal.signal(signal.SIGINT, sigint_handler) # restore custom handler

def parse_res(name, rel_path, base_url, dst_dir):
  logger().info(f"Parsing {name} with {{{rel_path=}}}")

  if not os.path.exists(f"{dst_dir}/{rel_path}/{name}"):
    logger().error(f"Unable to parse {rel_path}/{name}; file does not exist")
    return

  file = open(f"{dst_dir}/{rel_path}/{name}")
  while True:
    line = file.readline()
    if not line:
      break

    remoteName = line.strip().split(' ')[0]

    res_dir = DIR_MAPPINGS.get(os.path.splitext(remoteName)[1]) or ""
    fetch_file(f"{urljoin(rel_path, res_dir)}/{remoteName}", base_url, dst_dir)

def main(args):
  logger().info(f"Initialized with {args=}, base_url={BASE_URL}")

  if args.res:
    for client in CLIENTS:
      for name in RES_FILES:
        fetch_file(f"{RES_BASE_PATH}/{args.variation}/output_{args.res}/client/{client}/{name}", BASE_URL, args.out)
        if name in RES_PARSEABLE_FILES:
          parse_res(name, f"{RES_BASE_PATH}/{args.variation}/output_{args.res}/client/{client}", BASE_URL, args.out)

  if args.client:
    for client in CLIENTS:
      for name in CLIENT_FILES: 
        fetch_file(f"{CLIENT_BASE_PATH}/{args.variation}/output_{args.client}/{client}/General/{name}", BASE_URL, args.out)
        parse_res(name, f"{CLIENT_BASE_PATH}/{args.variation}/output_{args.client}/client/{client}", BASE_URL, args.out)

if __name__ == "__main__":
  parser = ArgumentParser(description="Fetches hot-patch resources for given version")
  parser.add_argument("variation", type=str, help="Variation name (eg. yspre_cb2plus_live)")
  parser.add_argument("--res", "-r", type=str, help="Resource version")
  parser.add_argument("--client", "-c", type=str, help="Client data version")
  parser.add_argument("--out", "-o", help="Output directory (defaults to ./resources)", type=str, default="./resources")
  parser.add_argument("--verbose", "-v", help="Be more verbose", action="store_true")
  args = parser.parse_args()

  logger().setLevel(logging.DEBUG if args.verbose else logging.INFO)
  handler = logging.StreamHandler()
  handler.setFormatter(logging.Formatter("[%(asctime)s] <%(levelname)s> %(message)s"))
  logger().addHandler(handler)

  signal.signal(signal.SIGINT, sigint_handler)

  sys.exit(main(args))