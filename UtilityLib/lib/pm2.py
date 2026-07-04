"""PM2Manager — YAML-driven PM2 process manager (Python port of pm2-servers.sh).

Config defaults to ~/.UtilityLib/pm2-servers.yml unless overridden with the
PM2_SERVERS_CONFIG environment variable or the config_path constructor argument.
"""

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
  import yaml as _YAML
except ImportError:
  _YAML = None

_SAMPLE_CONFIG = """\
# pm2-servers.yml
#
# Generated sample config.
# Edit this file, enable the projects you want, then rerun:
#   python -m UtilityLib.cli.pm2 --all
#   pm2-servers --all

version: 1

projects:
  - name: Example-Node
    enabled: false
    dir: ~/path/to/node-project
    port: 3000
    command: >
      source "$HOME/.nvm/nvm.sh" && nvm use 24 && npm run dev
    tunnels:
      - name: local-dev
        hostnames:
          - example.dev.yourdomain.info
    ssh:
      enabled: false
      name: Example-Node-ssh
      cwd: ~
      command: ssh some-host

  - name: Example-PHP
    enabled: false
    dir: ~/path/to/php-project
    port: 8080
    command: >
      php -S 0.0.0.0:8080 -t public
    tunnels:
      - name: local-dev
        hostnames:
          - example-php.dev.yourdomain.info

  - name: Example-Custom-Commands
    enabled: false
    dir: ~/path/to/project
    port: 3000
    command: npm run dev
    commands:
      start: "echo 'Custom start command' && npm run dev"
      stop: "echo 'Custom stop command' && pkill -f 'node.*dev'"
      restart: "echo 'Custom restart command' && pkill -f 'node.*dev' && npm run dev"
    tunnels:
      - name: local-dev
        hostnames:
          - example-custom.dev.yourdomain.info

  - name: Example-CMD-Manager
    enabled: false
    dir: ~/path/to/project
    port: 3000
    command: npm run dev
    manager: cmd
    tunnels:
      - name: local-dev
        hostnames:
          - example-cmd.dev.yourdomain.info
"""


@dataclass
class PM2Project:
  name: str
  directory: str
  port: int
  command: str
  subdomain: str = ""
  ssh_enabled: bool = False
  ssh_name: str = ""
  ssh_command: str = ""
  ssh_cwd: str = ""
  protected: bool = False  # if True: stop/restart via pm2s are blocked
  commands: Optional[Dict[str, str]] = None  # Custom commands: {"start": "...", "stop": "...", "restart": "..."}
  manager: str = "pm2"  # "pm2" (default) or "cmd" (terminal commands only)


class PM2Manager:
  """Python implementation of pm2-servers.sh — YAML-driven PM2 process manager.

  Config path resolution order:
    1. config_path constructor argument
    2. PM2_SERVERS_CONFIG environment variable
    3. ~/.UtilityLib/pm2-servers.yml (default)
  """

  DEFAULT_CONFIG = "~/.UtilityLib/pm2-servers.yml"

  def __init__(self, config_path: Optional[str] = None):
    _cfg = config_path or os.environ.get("PM2_SERVERS_CONFIG", self.DEFAULT_CONFIG)
    self.config_path = Path(_cfg).expanduser().resolve()

    self.show_pm2_status: bool = os.environ.get("SHOW_PM2_STATUS", "1") == "1"
    self.check_port_collisions: bool = os.environ.get("CHECK_PORT_COLLISIONS", "1") == "1"
    self.log_lines: int = int(os.environ.get("LOG_LINES", "50"))
    self.nvm_dir: Path = Path(os.environ.get("NVM_DIR", "~/.nvm")).expanduser()
    self.ecosystem_path: Path = Path(
      os.environ.get("ECOSYSTEM_DEFAULT_PATH", "~/pm2-ecosystem.config.js")
    ).expanduser()
    self._pm2_bin: Optional[str] = None
    self.projects: List[PM2Project] = []

    self._started: List[str] = []
    self._stopped: List[str] = []
    self._skipped: List[str] = []
    self._failed: List[str] = []
    self._state_changed: bool = False

  # ------------------------------------------------------------------ logging

  def _ts(self) -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  def _log(self, *msg):
    print(f"[{self._ts()}] {' '.join(str(m) for m in msg)}")

  def _warn(self, *msg):
    self._log("WARN:", *msg)

  def _error(self, *msg):
    print(f"[{self._ts()}] ERROR: {' '.join(str(m) for m in msg)}", file=sys.stderr)

  # ------------------------------------------------------------------ config

  @staticmethod
  def _expand(value: str) -> str:
    """Expand env vars and ~ in a path string."""
    return str(Path(os.path.expandvars(str(value))).expanduser())

  def _write_sample_config(self) -> bool:
    try:
      self.config_path.parent.mkdir(parents=True, exist_ok=True)
      self.config_path.write_text(_SAMPLE_CONFIG)
      return True
    except OSError as exc:
      self._error(f"Could not write sample config: {exc}")
      return False

  def load_config(self) -> bool:
    """Parse the YAML config and populate self.projects. Returns False on error."""
    if _YAML is None:
      self._error("pyyaml is required: pip install pyyaml")
      return False

    if not self.config_path.exists():
      self._warn(f"Config not found: {self.config_path}")
      if self._write_sample_config():
        self._warn(f"Created sample config at {self.config_path}")
        self._warn("Edit it, enable your projects, then rerun")
      return False

    try:
      data = _YAML.safe_load(self.config_path.read_text()) or {}
    except _YAML.YAMLError as exc:
      self._error(f"Failed to parse {self.config_path}: {exc}")
      return False

    raw = data.get("projects", [])
    if not isinstance(raw, list):
      self._error("'projects' must be a YAML list")
      return False

    seen: set = set()
    self.projects = []
    self._all_entries = []

    for entry in raw:
      if not isinstance(entry, dict):
        continue

      name = str(entry.get("name", "")).strip()
      if not name:
        self._error("A project entry is missing 'name'")
        return False
      if name in seen:
        self._error(f"Duplicate project name: {name}")
        return False
      seen.add(name)

      is_enabled = entry.get("enabled", True)
      self._all_entries.append((entry, is_enabled))

      if not is_enabled:
        continue

      subdomain = ""
      for tunnel in entry.get("tunnels", []):
        if not isinstance(tunnel, dict):
          continue
        for h in tunnel.get("hostnames", []):
          h = str(h).strip()
          if h:
            subdomain = h
            break
        if subdomain:
          break

      ssh = entry.get("ssh") or {}
      ssh_cwd_raw = ssh.get("cwd", "")
      ssh_cwd = self._expand(ssh_cwd_raw) if ssh_cwd_raw else self._expand(str(entry.get("dir", "")))

      self.projects.append(PM2Project(
        name=name,
        directory=self._expand(str(entry.get("dir", ""))),
        port=int(entry.get("port", 0)),
        command=str(entry.get("command", "")).strip(),
        subdomain=subdomain,
        ssh_enabled=bool(ssh.get("enabled", False)),
        ssh_name=str(ssh.get("name", "") or ""),
        ssh_command=str(ssh.get("command", "") or ""),
        ssh_cwd=ssh_cwd,
        protected=bool(entry.get("protected", False)),
        commands=entry.get("commands") or None,
        manager=str(entry.get("manager", "pm2")).strip(),
      ))

    if not self.projects:
      self._error(f"No enabled projects in {self.config_path}")
      return False

    return True

  def _find(self, name: str) -> Optional[PM2Project]:
    for p in self.projects:
      if p.name == name:
        return p
    return None

  def _find_any(self, name: str) -> Optional[PM2Project]:
    """Find a project by name, including disabled entries."""
    # First check already-loaded (enabled) projects
    proj = self._find(name)
    if proj:
      return proj
    # Parse disabled entries on demand
    for entry, is_enabled in getattr(self, '_all_entries', []):
      if not is_enabled and str(entry.get("name", "")).strip() == name:
        return self._parse_entry(entry)
    return None

  def _parse_entry(self, entry: dict) -> Optional[PM2Project]:
    """Parse a single YAML entry into a PM2Project."""
    name = str(entry.get("name", "")).strip()
    if not name:
      return None
    subdomain = ""
    for tunnel in entry.get("tunnels", []):
      if not isinstance(tunnel, dict):
        continue
      for h in tunnel.get("hostnames", []):
        h = str(h).strip()
        if h:
          subdomain = h
          break
      if subdomain:
        break
    ssh = entry.get("ssh") or {}
    ssh_cwd_raw = ssh.get("cwd", "")
    ssh_cwd = self._expand(ssh_cwd_raw) if ssh_cwd_raw else self._expand(str(entry.get("dir", "")))
    return PM2Project(
      name=name,
      directory=self._expand(str(entry.get("dir", ""))),
      port=int(entry.get("port", 0)),
      command=str(entry.get("command", "")).strip(),
      subdomain=subdomain,
      ssh_enabled=bool(ssh.get("enabled", False)),
      ssh_name=str(ssh.get("name", "") or ""),
      ssh_command=str(ssh.get("command", "") or ""),
      ssh_cwd=ssh_cwd,
      protected=bool(entry.get("protected", False)),
      commands=entry.get("commands") or None,
      manager=str(entry.get("manager", "pm2")).strip(),
    )

  # ------------------------------------------------------------------ pm2 binary

  def _ensure_pm2(self) -> bool:
    if self._pm2_bin and shutil.which(self._pm2_bin):
      return True
    found = shutil.which("pm2")
    if found:
      self._pm2_bin = found
      return True
    npm = shutil.which("npm")
    if not npm:
      self._error("pm2 not found and npm unavailable. Install Node.js/pm2.")
      return False
    self._log("pm2 not found — installing globally via npm…")
    r = subprocess.run(["npm", "install", "-g", "pm2"], check=False)
    if r.returncode != 0:
      self._error("Failed to install pm2 globally")
      return False
    found = shutil.which("pm2")
    if not found:
      self._error("pm2 still unavailable after installation")
      return False
    self._pm2_bin = found
    return True

  def _pm2(self, *args) -> subprocess.CompletedProcess:
    return subprocess.run([self._pm2_bin, *args], check=False)

  def _process_exists(self, name: str) -> bool:
    r = subprocess.run([self._pm2_bin, "describe", name], capture_output=True, check=False)
    return r.returncode == 0

  # ------------------------------------------------------------------ port check

  def _port_in_use(self, port: int) -> bool:
    if not self.check_port_collisions:
      return False
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
      return False

  # ------------------------------------------------------------------ interactive helpers

  def _confirm(self, prompt: str) -> bool:
    """Prompt for yes/no confirmation. Returns True for y/yes."""
    try:
      answer = input(f"{prompt} [y/N]: ").strip().lower()
      return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
      print()
      return False

  def _find_port_owners(self, port: int) -> List:
    """Return list of (pid, process_name) for ALL processes listening on port."""
    owners = []
    try:
      r = subprocess.run(
        ["lsof", "-ti", f":{port}"],
        capture_output=True, text=True, check=False,
      )
      for token in r.stdout.strip().split():
        try:
          pid = int(token)
          r2 = subprocess.run(
            ["ps", "-p", str(pid), "-o", "comm="],
            capture_output=True, text=True, check=False,
          )
          owners.append((pid, r2.stdout.strip()))
        except ValueError:
          pass
    except OSError:
      pass
    return owners

  def _kill_port_owner(self, port: int) -> bool:
    """Interactively kill all processes using port, wait for OS release. Returns True to continue."""
    owners = self._find_port_owners(port)
    if not owners:
      return True
    labels = [f"PID {pid}" + (f" ({name})" if name else "") for pid, name in owners]
    self._warn(f"Port {port} is in use by: {', '.join(labels)}")
    if not self._confirm(f"Kill {', '.join(labels)} and continue?"):
      return False
    for pid, _ in owners:
      try:
        os.kill(pid, 9)
      except ProcessLookupError:
        pass  # already gone
      except OSError as exc:
        self._error(f"Could not kill PID {pid}: {exc}")
        return False
    self._log(f"Killed: {', '.join(labels)} — waiting for port {port} to be released")
    for _ in range(8):
      time.sleep(0.5)
      if not self._port_in_use(port):
        return True
    self._error(f"Port {port} still bound 4s after kill — OS may need more time")
    return False

  # ------------------------------------------------------------------ validation

  @staticmethod
  def _is_ssh_only(proj: "PM2Project") -> bool:
    """True when this project is a standalone SSH connection (no main command)."""
    has_command = bool(proj.command) or bool(proj.commands)
    return proj.ssh_enabled and bool(proj.ssh_command) and not has_command

  def _validate(self, proj: PM2Project) -> bool:
    ssh_only = self._is_ssh_only(proj)
    # Allow either command OR commands (custom commands)
    has_command = bool(proj.command) or bool(proj.commands)
    if not proj.name or not proj.directory or (not has_command and not ssh_only):
      self._error(f"Project '{proj.name or 'unknown'}' is malformed (missing required fields)")
      return False
    if not os.path.isabs(proj.directory):
      self._error(f"{proj.name}: directory must resolve to an absolute path: {proj.directory}")
      return False
    if not ssh_only and not os.path.isdir(proj.directory):
      self._error(f"{proj.name}: directory does not exist: {proj.directory}")
      return False
    if proj.ssh_enabled and not proj.ssh_command:
      self._error(f"{proj.name}: ssh.enabled is true but ssh.command is empty")
      return False
    return True

  # ------------------------------------------------------------------ start / stop internals

  def _delete_existing(self, process_name: str) -> bool:
    if not self._process_exists(process_name):
      return True
    self._log(f"PM2 process '{process_name}' exists; recreating with latest config")
    r = self._pm2("delete", process_name)
    if r.returncode != 0:
      self._warn(f"pm2 delete failed for '{process_name}'")
      return False
    self._state_changed = True
    return True

  def _start_ssh_sidecar(self, proj: PM2Project) -> bool:
    if not proj.ssh_enabled:
      return True
    ssh_name = proj.ssh_name or f"{proj.name}-ssh"
    if not self._delete_existing(ssh_name):
      self._failed.append(f"{proj.name}: could not replace SSH sidecar '{ssh_name}'")
      return False
    bash = shutil.which("bash") or "/bin/bash"
    script = "set -e\ncd \"$1\"\nexec bash -lc \"$2\"\n"
    self._log(f"Starting SSH sidecar '{ssh_name}' for {proj.name}")
    r = subprocess.run([
      self._pm2_bin, "start", bash,
      "--name", ssh_name,
      "--interpreter", "none",
      "--cwd", proj.ssh_cwd,
      "--time",
      "--", "-c", script, "_", proj.ssh_cwd, proj.ssh_command,
    ], check=False)
    if r.returncode != 0:
      self._failed.append(f"{proj.name}: SSH sidecar start failed")
      return False
    self._state_changed = True
    return True

  def _stop_ssh_sidecar(self, proj: PM2Project):
    if not proj.ssh_enabled:
      return
    ssh_name = proj.ssh_name or f"{proj.name}-ssh"
    if not self._process_exists(ssh_name):
      return
    self._log(f"Stopping SSH sidecar '{ssh_name}'")
    r = self._pm2("stop", ssh_name)
    if r.returncode != 0:
      self._warn(f"pm2 stop failed for SSH sidecar '{ssh_name}'")
      return
    self._state_changed = True

  def _start_project(self, proj: PM2Project, action: str = "start") -> bool:
    if not self._ensure_pm2():
      self._failed.append(f"{proj.name}: pm2 unavailable")
      return False
    if not self._validate(proj):
      self._failed.append(f"{proj.name}: validation failed")
      return False

    already_exists = self._process_exists(proj.name)
    if proj.port and not already_exists and self._port_in_use(proj.port):
      if not self._kill_port_owner(proj.port):
        self._failed.append(f"{proj.name}: port {proj.port} could not be cleared")
        return False

    if action == "restart" and not already_exists:
      self._warn(f"{proj.name} not in PM2; starting instead")

    if not self._start_ssh_sidecar(proj):
      return False

    # ssh-only project: the SSH sidecar IS the project — no main process to start
    if self._is_ssh_only(proj):
      self._started.append(f"{proj.name} (SSH → {proj.ssh_command.strip()})")
      self._state_changed = True
      return True

    if not self._delete_existing(proj.name):
      self._failed.append(f"{proj.name}: could not replace existing PM2 process")
      return False

    bash = shutil.which("bash") or "/bin/bash"
    script = f"set -e\nexport PORT={proj.port}\ncd \"$1\"\nexec bash -lc \"$2\"\n"
    self._log(f"Starting {proj.name} from {proj.directory}")
    r = subprocess.run([
      self._pm2_bin, "start", bash,
      "--name", proj.name,
      "--interpreter", "none",
      "--cwd", proj.directory,
      "--time",
      "--", "-c", script, "_", proj.directory, proj.command,
    ], check=False)
    if r.returncode != 0:
      self._failed.append(f"{proj.name}: pm2 start failed")
      return False

    label = (
      f"{proj.name} ({proj.subdomain} -> http://localhost:{proj.port})"
      if proj.subdomain else
      f"{proj.name} (http://localhost:{proj.port})"
    )
    self._started.append(label)
    self._state_changed = True
    return True

  def _stop_project(self, proj: PM2Project) -> bool:
    if proj.protected:
      self._warn(f"{proj.name} is protected — skipping stop (use `pm2 stop {proj.name}` directly)")
      self._skipped.append(f"{proj.name}: protected")
      return True
    if not self._ensure_pm2():
      self._failed.append(f"{proj.name}: pm2 unavailable")
      return False

    # ssh-only project: the SSH sidecar IS the process — stop it directly
    if self._is_ssh_only(proj):
      self._stop_ssh_sidecar(proj)
      self._stopped.append(proj.name)
      self._state_changed = True
      return True

    if not self._process_exists(proj.name):
      self._skipped.append(f"{proj.name}: not found in PM2")
      self._warn(f"{proj.name} is not managed by PM2")
      return True
    self._log(f"Stopping {proj.name}")
    r = self._pm2("stop", proj.name)
    if r.returncode != 0:
      self._failed.append(f"{proj.name}: pm2 stop failed")
      return False
    self._stop_ssh_sidecar(proj)
    self._stopped.append(proj.name)
    self._state_changed = True
    return True

  # ------------------------------------------------------------------ public API

  def _reset(self):
    self._started = []
    self._stopped = []
    self._skipped = []
    self._failed = []
    self._state_changed = False

  def start(self, name: str) -> bool:
    """Start a single named project via PM2 or terminal commands."""
    proj = self._find_any(name)
    if not proj:
      self._error(f"Project not found: {name}")
      return False
    
    # Check for custom start command
    if proj.commands and "start" in proj.commands:
      custom_cmd = proj.commands["start"]
      self._log(f"Starting {name} with custom command: {custom_cmd}")
      r = subprocess.run(["bash", "-lc", custom_cmd], cwd=proj.directory, check=False)
      if r.returncode != 0:
        self._failed.append(f"{name}: custom start command failed")
        return False
      self._started.append(f"{name} (custom command)")
      self._state_changed = True
      return True
    
    # For cmd manager, use the command field directly
    if proj.manager == "cmd":
      if not proj.command:
        self._error(f"{name}: manager is 'cmd' but no command specified")
        return False
      self._log(f"Starting {name} with command: {proj.command}")
      r = subprocess.run(["bash", "-lc", proj.command], cwd=proj.directory, check=False)
      if r.returncode != 0:
        self._failed.append(f"{name}: command failed")
        return False
      self._started.append(f"{name} (cmd manager)")
      self._state_changed = True
      return True
    
    # Default PM2 management
    return self._start_project(proj, "start")

  def stop(self, name: str) -> bool:
    """Stop a single named project via PM2 or terminal commands."""
    proj = self._find_any(name)
    if not proj:
      self._error(f"Project not found: {name}")
      return False
    
    # Check for custom stop command
    if proj.commands and "stop" in proj.commands:
      custom_cmd = proj.commands["stop"]
      self._log(f"Stopping {name} with custom command: {custom_cmd}")
      r = subprocess.run(["bash", "-lc", custom_cmd], cwd=proj.directory, check=False)
      if r.returncode != 0:
        self._failed.append(f"{name}: custom stop command failed")
        return False
      self._stopped.append(f"{name} (custom command)")
      self._state_changed = True
      return True
    
    # For cmd manager, we can't really stop - just log it
    if proj.manager == "cmd":
      self._warn(f"{name}: manager is 'cmd' - stop not supported (use custom commands)")
      self._skipped.append(f"{name}: cmd manager doesn't support stop")
      return True
    
    return self._stop_project(proj)

  def restart(self, name: str) -> bool:
    """Restart (delete + re-start) a single named project via PM2 or terminal commands."""
    proj = self._find_any(name)
    if not proj:
      self._error(f"Project not found: {name}")
      return False
    if proj.protected:
      self._warn(f"{name} is protected — skipping restart (use `pm2 restart {name}` directly)")
      self._skipped.append(f"{name}: protected")
      return True
    
    # Check for custom restart command
    if proj.commands and "restart" in proj.commands:
      custom_cmd = proj.commands["restart"]
      self._log(f"Restarting {name} with custom command: {custom_cmd}")
      r = subprocess.run(["bash", "-lc", custom_cmd], cwd=proj.directory, check=False)
      if r.returncode != 0:
        self._failed.append(f"{name}: custom restart command failed")
        return False
      self._started.append(f"{name} (custom restart)")
      self._state_changed = True
      return True
    
    # For cmd manager, we can't really restart - just log it
    if proj.manager == "cmd":
      self._warn(f"{name}: manager is 'cmd' - restart not supported (use custom commands)")
      self._skipped.append(f"{name}: cmd manager doesn't support restart")
      return True
    
    # Default PM2 management
    return self._start_project(proj, "restart")

  def start_all(self) -> bool:
    """Start all enabled projects."""
    ok = True
    for proj in self.projects:
      if not self._start_project(proj, "start"):
        ok = False
    # Auto-sync ecosystem.config.js so it never goes stale
    try:
      eco = self.generate_ecosystem()
      self.ecosystem_path.write_text(eco)
      self._log(f"Ecosystem config saved to {self.ecosystem_path}")
    except Exception:
      pass
    return ok

  def stop_all(self) -> bool:
    """Stop all enabled projects."""
    ok = True
    for proj in self.projects:
      if not self._stop_project(proj):
        ok = False
    return ok

  def get_processes(self) -> List[Dict]:
    """Return pm2 process list as a list of dicts (from pm2 jlist). Empty list on error."""
    import json as _json
    if not self._ensure_pm2():
      return []
    r = subprocess.run([self._pm2_bin, "jlist"], capture_output=True, text=True, check=False)
    if r.returncode != 0 or not r.stdout.strip():
      pm2_processes = []
    else:
      try:
        pm2_processes = _json.loads(r.stdout) or []
      except ValueError:
        pm2_processes = []
    
    # Add custom command processes that aren't in PM2
    pm2_names = {p.get("name") for p in pm2_processes}
    for proj in self.projects:
      if proj.commands and proj.name not in pm2_names:
        # Check if custom command process is running
        status = self._check_custom_command_status(proj)
        if status:
          pm2_processes.append({
            "name": proj.name,
            "pm2_env": {
              "status": status,
              "pm_uptime": None,
              "restart_time": 0,
            },
            "monit": {
              "cpu": 0,
              "memory": 0,
            },
            "pid": None,
          })
    
    return pm2_processes
  
  def _check_custom_command_status(self, proj: PM2Project) -> str:
    """Check if a project with custom commands is running."""
    if not proj.commands:
      return "not started"
    
    # For Hermes, check the gateway status
    if "hermes" in proj.name.lower():
      try:
        hermes_path = f"{proj.directory}/venv/bin/hermes"
        r = subprocess.run(
          ["bash", "-lc", f"{hermes_path} gateway status"],
          cwd=proj.directory,
          capture_output=True,
          text=True,
          check=False
        )
        if r.returncode == 0 and "PID" in r.stdout:
          return "online"
        else:
          return "stopped"
      except Exception:
        return "unknown"
    
    # For other custom commands, try to infer status
    return "unknown"

  def _fmt_uptime(self, pm_uptime_ms) -> str:
    if not pm_uptime_ms:
      return "-"
    secs = (datetime.now().timestamp() * 1000 - pm_uptime_ms) / 1000
    if secs < 0:
      return "-"
    h, rem = divmod(int(secs), 3600)
    m, s = divmod(rem, 60)
    if h:
      return f"{h}h {m}m"
    if m:
      return f"{m}m {s}s"
    return f"{s}s"
  
  def _fmt_mem(self, bytes_val) -> str:
    try:
      mb = int(bytes_val) / 1024 / 1024
      return f"{mb:.1f} MB"
    except (TypeError, ValueError):
      return "-"
  
  def list_status(self) -> bool:
    """Print PM2 process list including custom command processes."""
    if not self._ensure_pm2():
      return False
    
    # Get enhanced process list including custom commands
    processes = self.get_processes()
    
    if not processes:
      print("No processes running")
      return True
    
    # Print header
    print(f"{'┌─':─<1}{'┬─':─<20}{'┬─':─<12}{'┬─':─<8}{'┬─':─<8}{'┬─':─<10}{'┬─':─<8}{'┬─':─<6}{'┬─':─<11}{'┬─':─<8}{'┬─':─<8}{'┬─':─<8}{'┬─':─<8}{'┐'}")
    print(f"{'│ id':<3}{'│ name':<20}{'│ namespace':<12}{'│ version':<8}{'│ mode':<8}{'│ pid':<10}{'│ uptime':<8}{'│ ↺':<6}{'│ status':<11}{'│ cpu':<8}{'│ mem':<8}{'│ user':<8}{'│ watching':<8}{'│'}")
    print(f"{'├─':─<1}{'┼─':─<20}{'┼─':─<12}{'┼─':─<8}{'┼─':─<8}{'┼─':─<10}{'┼─':─<8}{'┼─':─<6}{'┼─':─<11}{'┼─':─<8}{'┼─':─<8}{'┼─':─<8}{'┼─':─<8}{'┤'}")
    
    for proc in processes:
      name = proc.get("name", "?")
      pid = str(proc.get("pid") or "-")
      env = proc.get("pm2_env", {})
      status = env.get("status", "unknown")
      monit = proc.get("monit", {})
      cpu = f"{monit.get('cpu', 0):.1f}%"
      mem = self._fmt_mem(monit.get("memory", 0))
      uptime = self._fmt_uptime(env.get("pm_uptime")) if status == "online" else "-"
      restarts = str(env.get("restart_time", 0))
      
      print(f"│ {pid:<3}│ {name:<20}│ {'default':<12}│ {'N/A':<8}│ {'fork':<8}│ {pid:<10}│ {uptime:<8}│ {restarts:<6}│ {status:<11}│ {cpu:<8}│ {mem:<8}│ {'vishalk…':<8}│ {'disabled':<8}│")
    
    print(f"{'└─':─<1}{'┴─':─<20}{'┴─':─<12}{'┴─':─<8}{'┴─':─<8}{'┴─':─<10}{'┴─':─<8}{'┴─':─<6}{'┴─':─<11}{'┴─':─<8}{'┴─':─<8}{'┴─':─<8}{'┴─':─<8}{'┘'}")
    return True

  def logs(self, name: str) -> bool:
    """Stream recent logs for a named project."""
    proj = self._find_any(name)
    if not proj:
      self._error(f"Project not found: {name}")
      return False
    if not self._ensure_pm2():
      return False
    if not self._process_exists(name):
      self._error(f"{name} is not managed by PM2")
      return False
    subprocess.run(
      [self._pm2_bin, "logs", name, "--lines", str(self.log_lines), "--nostream"],
      check=False,
    )
    return True

  def run_foreground(self, name: str) -> int:
    """Run a project in the foreground (blocking). Returns process exit code."""
    proj = self._find_any(name)
    if not proj:
      self._error(f"Project not found: {name}")
      return 1
    if not self._validate(proj):
      return 1
    if self._port_in_use(proj.port):
      self._warn(f"Port {proj.port} already in use")
      return 1

    if proj.ssh_enabled:
      def _ssh():
        subprocess.run(["bash", "-lc", proj.ssh_command], cwd=proj.ssh_cwd, check=False)
      threading.Thread(target=_ssh, daemon=True).start()

    self._log(f"Running {proj.name} in foreground from {proj.directory}")
    r = subprocess.run(["bash", "-lc", proj.command], cwd=proj.directory, check=False)
    return r.returncode

  # ------------------------------------------------------------------ ecosystem generation

  @staticmethod
  def _js_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")

  def generate_ecosystem(self) -> str:
    """Return a PM2 ecosystem.config.js string generated from the loaded projects."""
    lines = [
      f"// Generated from {self.config_path}",
      "// Keep the YAML config as the reusable source of truth.",
      "// Usage: pm2 start ecosystem.config.js",
      "",
      "module.exports = {",
      "  apps: [",
    ]
    for i, proj in enumerate(self.projects):
      comma = "," if i < len(self.projects) - 1 else ""
      lines += [
        f"    // {proj.name}",
        "    {",
        f"      name: '{self._js_escape(proj.name)}',",
        "      script: 'bash',",
        f"      args: ['-lc', '{self._js_escape(proj.command)}'],",
        f"      cwd: '{self._js_escape(proj.directory)}',",
        "      interpreter: 'none',",
        "      instances: 1,",
        "      exec_mode: 'fork'",
        f"    }}{comma}",
        "",
      ]
    lines += [
      "  ]",
      "};",
      "",
      f"// Reusable config: {self.config_path}",
      f"// Suggested output: {self.ecosystem_path}",
      "// Start:   pm2 start ~/pm2-ecosystem.config.js",
      "// Restart: pm2 restart ~/pm2-ecosystem.config.js",
    ]
    return "\n".join(lines) + "\n"

  # ------------------------------------------------------------------ finalize

  def _save_pm2(self):
    if not self._state_changed:
      return
    if not self._ensure_pm2():
      return
    self._log("Saving PM2 process list")
    r = self._pm2("save")
    if r.returncode != 0:
      self._warn("pm2 save failed")
      return
    if self.show_pm2_status:
      self._log("Current PM2 status")
      self._pm2("status")

  def summary(self) -> str:
    """Return a human-readable operation summary string."""
    if not any([self._started, self._stopped, self._skipped, self._failed]):
      return ""
    lines = ["\nSummary"]
    lines.append(f"Started: {len(self._started)}")
    for item in self._started:
      lines.append(f"  - {item}")
    lines.append(f"Stopped: {len(self._stopped)}")
    for item in self._stopped:
      lines.append(f"  - {item}")
    lines.append(f"Skipped: {len(self._skipped)}")
    for item in self._skipped:
      lines.append(f"  - {item}")
    lines.append(f"Failed: {len(self._failed)}")
    for item in self._failed:
      lines.append(f"  - {item}")
    return "\n".join(lines)

  def finalize(self) -> bool:
    """Save PM2 state, print summary, and return True if no failures."""
    self._save_pm2()
    s = self.summary()
    if s:
      print(s)
    return len(self._failed) == 0
