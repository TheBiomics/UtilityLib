"""CloudflaredManager — Cloudflare Tunnel local config manager.

Manages ~/.cloudflared/*.yml ingress rules: read, update, reload.
Can be used independently of PM2Manager.

Usage::

    from UtilityLib.lib.cloudflared import CloudflaredManager

    cf = CloudflaredManager()
    print(cf.load_routes())                        # {hostname: service, ...}
    conflicts = cf.conflicts({"foo.example.com": "http://localhost:3000"})
    if conflicts:
        cf.apply_updates(conflicts)                # rewrites YAML + reloads daemon
"""

import os
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
  import yaml as _YAML
except ImportError:
  _YAML = None


class CloudflaredManager:
  """Manages local Cloudflare Tunnel configuration files.

  Config directory resolution order:
    1. config_dir constructor argument
    2. CLOUDFLARED_CONFIG_DIR environment variable
    3. ~/.cloudflared (default)
  """

  DEFAULT_CONFIG_DIR = "~/.cloudflared"

  def __init__(self, config_dir: Optional[str] = None):
    _dir = config_dir or os.environ.get("CLOUDFLARED_CONFIG_DIR", self.DEFAULT_CONFIG_DIR)
    self.config_dir = Path(_dir).expanduser().resolve()

  # ------------------------------------------------------------------ logging

  def _ts(self) -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  def _log(self, *msg):
    print(f"[{self._ts()}] {' '.join(str(m) for m in msg)}")

  def _warn(self, *msg):
    self._log("WARN:", *msg)

  def _error(self, *msg):
    print(f"[{self._ts()}] ERROR: {' '.join(str(m) for m in msg)}", file=sys.stderr)

  # ------------------------------------------------------------------ config files

  def _config_files(self) -> List[Path]:
    if not self.config_dir.is_dir():
      return []
    return sorted(self.config_dir.glob("*.y*ml"))

  # ------------------------------------------------------------------ public API

  def load_routes(self) -> Dict[str, str]:
    """Return {hostname: service} parsed from all ingress rules in config_dir."""
    if _YAML is None:
      self._error("pyyaml is required: pip install pyyaml")
      return {}
    routes: Dict[str, str] = {}
    for cf in self._config_files():
      try:
        data = _YAML.safe_load(cf.read_text()) or {}
        for rule in data.get("ingress", []):
          if not isinstance(rule, dict):
            continue
          h = str(rule.get("hostname", "")).strip()
          s = str(rule.get("service", "")).strip()
          if h and s:
            routes[h] = s
      except Exception:
        pass
    return routes

  def update_route(self, hostname: str, new_service: str) -> Optional[Path]:
    """Rewrite the ingress service for hostname in the first matching config file.

    Returns the Path of the updated file, or None if hostname was not found.
    """
    if _YAML is None:
      return None
    for cf in self._config_files():
      try:
        data = _YAML.safe_load(cf.read_text()) or {}
        changed = False
        for rule in data.get("ingress", []):
          if isinstance(rule, dict) and rule.get("hostname", "").strip() == hostname:
            rule["service"] = new_service
            changed = True
            break
        if changed:
          cf.write_text(_YAML.dump(data, default_flow_style=False, allow_unicode=True))
          self._log(f"Updated {cf.name}: {hostname} → {new_service}")
          return cf
      except Exception as exc:
        self._warn(f"Could not update {cf}: {exc}")
    return None

  def reload(self) -> bool:
    """Reload the running cloudflared daemon (SIGHUP, then CLI fallback).

    Returns True if the reload signal was delivered, False if cloudflared is not running.
    """
    r = subprocess.run(
      ["pgrep", "-x", "cloudflared"],
      capture_output=True, text=True, check=False,
    )
    pids = [int(p) for p in r.stdout.strip().split() if p.isdigit()]
    if pids:
      for pid in pids:
        try:
          os.kill(pid, signal.SIGHUP)
        except OSError:
          pass
      self._log(
        f"Sent SIGHUP to cloudflared "
        f"(PID {', '.join(str(p) for p in pids)}) — config reloaded"
      )
      return True

    cf_bin = shutil.which("cloudflared")
    if cf_bin:
      r2 = subprocess.run([cf_bin, "tunnel", "reload"], capture_output=True, check=False)
      if r2.returncode == 0:
        self._log("cloudflared tunnel reloaded via CLI")
        return True

    self._warn("cloudflared is not running — start or restart it manually to apply changes")
    return False

  def conflicts(self, desired: Dict[str, str]) -> List[Tuple[str, str, str]]:
    """Compare desired {hostname: service} with the current config.

    Returns a list of (hostname, current_service, desired_service) for every
    hostname whose current mapping differs from what is desired.
    """
    existing = self.load_routes()
    result = []
    for hostname, new_svc in desired.items():
      current = existing.get(hostname)
      if current and current.rstrip("/") != new_svc.rstrip("/"):
        result.append((hostname, current, new_svc))
    return result

  def apply_updates(self, updates: List[Tuple[str, str, str]]) -> bool:
    """Apply route updates and reload cloudflared.

    updates: list of (hostname, current_service, desired_service) as returned
             by conflicts().
    Returns True if at least one config file was rewritten.
    """
    any_updated = False
    for hostname, _, desired_svc in updates:
      updated = self.update_route(hostname, desired_svc)
      if updated:
        any_updated = True
      else:
        self._warn(f"No cloudflared config entry found for {hostname} — update manually")
    if any_updated:
      self.reload()
    return any_updated
