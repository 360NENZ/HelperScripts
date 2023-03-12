#!/usr/bin/python3
import sys
import os
import json
import requests
import logging
import signal
from shutil import copyfileobj
from posixpath import join as urljoin
from argparse import ArgumentParser

BASE_URL = "https://autopatchhk.yuanshen.com"

CLIENTS = [
  "Android",
  "StandaloneWindows64",
  "iOS",
  "PS5",
  "PS4"
]

RES_BASE_PATH = "client_game_res"
RES_FILES = [
  "res_versions_external",
  "res_versions_medium",
  "res_versions_streaming",
  "release_res_versions_external",
  "release_res_versions_medium",
  "release_res_versions_streaming",
  "base_revision",
  "script_version",
  "AudioAssets/audio_versions",
  "VideoAssets/video_versions"
]
RES_PARSEABLE_FILES = [
  "res_versions_external",
  "release_res_versions_external",
  "AudioAssets/audio_versions",
  "VideoAssets/video_versions"
]
RES_BASE_SKIPPABLE = [
  "AudioAssets/audio_versions",
  "VideoAssets/video_versions"
]

SILENCE_BASE_PATH = "client_design_data"
SILENCE_FILES = [
  "AssetBundles/data_versions"
]

CLIENT_BASE_PATH = "client_design_data"
CLIENT_FILES = [
  "AssetBundles/data_versions"
]

DIR_MAPPINGS = {
  ".blk": "AssetBundles",
  ".pck": "AudioAssets",
  ".cuepoint": "VideoAssets",
  ".usm": "VideoAssets"
}
NAME_MAPPINGS = {
  "svc_catalog": "AssetBundles"
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

def parse_json(name, rel_path, base_url, dst_dir, is_base):
  logger().info(f"Parsing {name} with {{{rel_path=}, {is_base=}}}")

  if not os.path.exists(f"{dst_dir}/{rel_path}/{name}"):
    logger().error(f"Unable to parse {rel_path}/{name}; file does not exist")
    return

  if is_base and name in RES_BASE_SKIPPABLE:
    logger().debug(f"Skipping {name} because {is_base=}; resources already fetched")
    return

  file = open(f"{dst_dir}/{rel_path}/{name}")
  while True:
    line = file.readline()
    if not line:
      break

    resource = json.loads(line.strip())
    if is_base == False and (name not in SILENCE_FILES and name not in CLIENT_FILES) and resource.get("isPatch") != True:
      continue # revision is not base, resource is not silence and file is not marked as updated

    res_dir = DIR_MAPPINGS.get(os.path.splitext(resource["remoteName"])[1]) or NAME_MAPPINGS.get(resource["remoteName"]) or ""
    fetch_file(f"{urljoin(rel_path, res_dir)}/{resource['remoteName']}", base_url, dst_dir)

def main(args):
  logger().info(f"Initialized with {args=}, base_url={BASE_URL}")

  if args.res:
    for client in CLIENTS:
      for name in RES_FILES:
        fetch_file(f"{RES_BASE_PATH}/{args.variation}/output_{args.res}/client/{client}/{name}", BASE_URL, args.out)
        if name in RES_PARSEABLE_FILES:
          parse_json(name, f"{RES_BASE_PATH}/{args.variation}/output_{args.res}/client/{client}", BASE_URL, args.out, args.base)
  elif args.base:
    logger().warning("Setting --base has no effect when not fetching resources!")

  if args.client:
    for name in CLIENT_FILES: 
      fetch_file(f"{CLIENT_BASE_PATH}/{args.variation}/output_{args.client}/client/General/{name}", BASE_URL, args.out)
      parse_json(name, f"{CLIENT_BASE_PATH}/{args.variation}/output_{args.client}/client/General", BASE_URL, args.out, args.base)

  if args.silence:
    for name in SILENCE_FILES:
      fetch_file(f"{SILENCE_BASE_PATH}/{args.variation}/output_{args.silence}/client_silence/General/{name}", BASE_URL, args.out)
      parse_json(name, f"{SILENCE_BASE_PATH}/{args.variation}/output_{args.silence}/client_silence/General", BASE_URL, args.out, args.base)

if __name__ == "__main__":
  parser = ArgumentParser(description="Fetches hot-patch resources for given version")
  parser.add_argument("variation", type=str, help="Variation name (eg. 3.2_live)")
  parser.add_argument("--res", "-r", type=str, help="Resource version in format of {$version}_{$suffix}")
  parser.add_argument("--client", "-c", type=str, help="Client data version in format of {$version}_{$suffix}")
  parser.add_argument("--silence", "-s", type=str, help="Silence version in format of {$version}_{$suffix}")
  parser.add_argument("--base", "-b", help="Whether given revision is base (will attempt to fetch all resources)", action="store_true")
  parser.add_argument("--out", "-o", help="Output directory (defaults to ./resources)", type=str, default="./resources")
  parser.add_argument("--verbose", "-v", help="Be more verbose", action="store_true")
  args = parser.parse_args()

  logger().setLevel(logging.DEBUG if args.verbose else logging.INFO)
  handler = logging.StreamHandler()
  handler.setFormatter(logging.Formatter("[%(asctime)s] <%(levelname)s> %(message)s"))
  logger().addHandler(handler)

  signal.signal(signal.SIGINT, sigint_handler)

  sys.exit(main(args))