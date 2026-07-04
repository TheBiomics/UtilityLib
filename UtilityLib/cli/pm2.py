#!/usr/bin/env python3
"""
PM2 CLI — YAML-driven PM2 process manager

Config: ~/.UtilityLib/pm2-servers.yml (or PM2_SERVERS_CONFIG env var)

Usage:
  pm2s <project>                  Start project (background)
  pm2s --no-bg <project>          Start project (foreground)
  pm2s --all  / pm2s -a           List all projects from YAML (enabled + disabled)
  pm2s --start-all                 Start all enabled projects
  pm2s --stop <project>            Stop a project
  pm2s --stop-all                  Stop all projects
  pm2s --restart <project>         Restart a named project
  pm2s --list  / pm2s -ls          Show live PM2 process status
  pm2s --logs <project>            Show recent logs
  pm2s --generate-ecosystem        Print PM2 ecosystem.config.js
  pm2s --config <path> / pm2s -c   Use a custom config file

Tunnel:
  The Cloudflare tunnel is just another PM2 project (Cloudflared).
  Control it like any other project:
    pm2s Cloudflared                Start tunnel
    pm2s --stop Cloudflared         Stop tunnel
    pm2s --restart Cloudflared      Restart tunnel
"""

import sys
from ..lib.pm2 import PM2Manager
from ..lib.cmd import CMDLib


def list_yaml_projects(mgr):
  """Print all YAML project names with status."""
  all_entries = getattr(mgr, '_all_entries', [])
  if not all_entries:
    print("No projects found in config.")
    return
  print(f"{'PROJECT':<30} {'STATUS':<10} {'PORT':<6} {'TUNNEL HOSTNAME'}")
  print("-" * 70)
  for entry, is_enabled in all_entries:
    name = str(entry.get("name", "")).strip()
    port = str(entry.get("port", "")) if entry.get("port") else ""
    status = "enabled" if is_enabled else "disabled"
    hostname = ""
    for tunnel in entry.get("tunnels", []):
      if isinstance(tunnel, dict):
        for h in tunnel.get("hostnames", []):
          hostname = str(h).strip()
          break
      if hostname:
        break
    print(f"{name:<30} {status:<10} {port:<6} {hostname}")


def main():
  parser = CMDLib.init_cli(
    version="UtilityLib.PM3 v1.0",
    description="YAML-driven PM2 process manager",
  )

  # Mode flags (mutually exclusive actions)
  group = parser.add_mutually_exclusive_group()
  group.add_argument("--all", "-a", dest="show_all", action="store_true", help="List all projects from YAML (enabled + disabled)")
  group.add_argument("--start-all", action="store_true", help="Start all enabled projects")
  group.add_argument("--stop", metavar="PROJECT", help="Stop a named project")
  group.add_argument("--stop-all", action="store_true", help="Stop all projects")
  group.add_argument("--restart", metavar="PROJECT", help="Restart a named project")
  group.add_argument("--list", "-ls", action="store_true", help="Show live PM2 process status")
  group.add_argument("--logs", metavar="PROJECT", help="Show recent PM2 logs for a project")
  group.add_argument("--generate-ecosystem", action="store_true", help="Print PM2 ecosystem.config.js to stdout")

  # Optional modifiers
  parser.add_argument("--no-bg", action="store_true", help="Run project in foreground (single project only)")
  parser.add_argument("--config", "-c", metavar="PATH", help="Path to YAML config (default: ~/.UtilityLib/pm2-servers.yml)")
  parser.add_argument("project", nargs="?", help="Project name to start (default action when no flag given)")

  args = parser.parse_args()

  mgr = PM2Manager(config_path=args.config)

  # --all / -a: list all YAML project names
  if args.show_all:
    if not mgr.load_config():
      sys.exit(1)
    list_yaml_projects(mgr)
    sys.exit(0)

  # --generate-ecosystem and --list don't need a project name
  if args.generate_ecosystem or args.list:
    if not mgr.load_config():
      sys.exit(1)
    if args.generate_ecosystem:
      print(mgr.generate_ecosystem(), end="")
      sys.exit(0)
    if args.list:
      sys.exit(0 if mgr.list_status() else 1)

  # --logs
  if args.logs:
    if not mgr.load_config():
      sys.exit(1)
    sys.exit(0 if mgr.logs(args.logs) else 1)

  # --stop / --stop-all
  if args.stop_all:
    if not mgr.load_config():
      sys.exit(1)
    mgr._reset()
    ok = mgr.stop_all()
    mgr.finalize()
    sys.exit(0 if ok else 1)

  if args.stop:
    if not mgr.load_config():
      sys.exit(1)
    mgr._reset()
    ok = mgr.stop(args.stop)
    mgr.finalize()
    sys.exit(0 if ok else 1)

  # --restart
  if args.restart:
    if not mgr.load_config():
      sys.exit(1)
    mgr._reset()
    ok = mgr.restart(args.restart)
    mgr.finalize()
    sys.exit(0 if ok else 1)

  # --start-all
  if args.start_all:
    if args.no_bg:
      print("ERROR: --no-bg is only supported with a single project name.", file=sys.stderr)
      sys.exit(1)
    if not mgr.load_config():
      sys.exit(1)
    mgr._reset()
    ok = mgr.start_all()
    mgr.finalize()
    sys.exit(0 if ok else 1)

  # Single project name
  if not args.project:
    parser.print_help()
    sys.exit(1)

  if not mgr.load_config():
    sys.exit(1)

  if args.no_bg:
    code = mgr.run_foreground(args.project)
    sys.exit(code)

  mgr._reset()
  ok = mgr.start(args.project)
  mgr.finalize()
  sys.exit(0 if ok else 1)


if __name__ == "__main__":
  main()
