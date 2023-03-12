#!/usr/bin/python3
import sys
import json
from argparse import ArgumentParser

COVER_SWITCH_DATA = {
  "gacha": 1,
  "mall": 2,
  "battle_pass": 3,
  "bulletin": 4,
  "mail": 5,
  "time": 6,
  "community": 7,
  "handbook": 8,
  "feedback": 9,
  "quest": 10,
  "map": 11,
  "team": 12,
  "friends": 13,
  "avatar_list": 14,
  "character": 15,
  "activity": 16,
  "multiplayer": 17,
  "recharge_card": 18,
  "exchange_code": 19,
  "guide_rating": 20,
  "share": 21,
  "mcoin": 22,
  "battle_pass_recharge": 23,
  "achievement": 24,
  "photograph": 25,
  "network_latency_icon": 26,
  "user_center": 27,
  "account_binding": 28,
  "recommend_panel": 29,
  "codex": 30,
  "report": 31,
  "derivative_mall": 32,
  "edit_name": 33,
  "edit_signature": 34,
  "resin_card": 35,
  "file_integrity_check": 36,
  "activity_h5": 37,
  "survey": 38,
  "concert_package": 39,
  "cloud_game": 40,
  "battle_pass_discount": 41,
  "share_bbs": 42
}

NET_DELAY_CONFIG = {
  "gateserver": "openGateserver"
}

def main(args):
  custom_config = {
    "coverSwitch": [],
    "mtrConfig": {},
    "reportNetDelayConfig": {}
  }

  # cover
  for switch in args.cover_switches or []:
    custom_config["coverSwitch"].append(COVER_SWITCH_DATA[switch[0]])
  # home item
  if args.home_item_filter:
    custom_config["homeItemFilter"] = args.home_item_filter
  # mtr
  custom_config["mtrConfig"] = {"isOpen": args.mtr_enable}
  if args.mtr_max_ttl:
    custom_config["mtrConfig"]["maxTTL"] = args.mtr_max_ttl
  if args.mtr_timeout:
    custom_config["mtrConfig"]["timeOut"] = args.mtr_timeout
  if args.mtr_trace_count:
    custom_config["mtrConfig"]["traceCount"] = args.mtr_trace_count
  if args.mtr_abort_timeout_count:
    custom_config["mtrConfig"]["abortTimeOutCount"] = args.mtr_abort_timeout_count
  if args.mtr_auto_trace_interval:
    custom_config["mtrConfig"]["autoTraceInterval"] = args.mtr_auto_trace_interval
  # net delay
  for config in args.net_delay or []:
    custom_config["reportNetDelayConfig"][NET_DELAY_CONFIG[config[0]]] = True

  print(json.dumps(custom_config, separators=(',', ':')))

if __name__ == "__main__":
  parser = ArgumentParser(description="Generates region client custom config")
  parser.add_argument("--cover", "-c", dest='cover_switches', type=str, action="append", help="Hide specific feature", choices=COVER_SWITCH_DATA.keys(), nargs='*')
  parser.add_argument("--home-item-filter", type=int, help="???")
  parser.add_argument("--mtr-enable", action='store_true', help="???")
  parser.add_argument("--mtr-max-ttl", type=int, help="???")
  parser.add_argument("--mtr-timeout", type=int, help="???")
  parser.add_argument("--mtr-trace-count", type=int, help="???")
  parser.add_argument("--mtr-abort-timeout-count", type=int, help="???")
  parser.add_argument("--mtr-auto-trace-interval", type=int, help="???")
  parser.add_argument("--report-net-delay", "-n", dest='net_delay', type=str, action="append", help="???", choices=NET_DELAY_CONFIG.keys(), nargs='*')

  sys.exit(main(parser.parse_args()))
