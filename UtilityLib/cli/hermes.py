"""
UtilityLib CLI — Hermes plugin manager.

Usage:
    python -m UtilityLib.cli.hermes install-all
    python -m UtilityLib.cli.hermes install <name>
    python -m UtilityLib.cli.hermes list
    python -m UtilityLib.cli.hermes status
"""

import argparse
import os
import shutil
import sys


def _get_plugin_dir():
    """Get the directory where h5_wall source files live."""
    module_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(module_dir, "..", "h5_wall")


def _get_target_dir():
    """Get the Hermes profile plugins directory."""
    return os.path.expanduser("~/.hermes/profiles/h5/plugins")


def _list_plugins(base):
    """List plugin directories (with __init__.py and plugin.yaml)."""
    result = []
    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name)
        if os.path.isdir(path) and not name.startswith("_"):
            if os.path.exists(os.path.join(path, "__init__.py")):
                result.append(name)
    return result


def _get_plugin_meta(plugin_dir):
    """Read plugin.yaml for metadata."""
    yaml_path = os.path.join(plugin_dir, "plugin.yaml")
    if os.path.exists(yaml_path):
        try:
            import yaml
            with open(yaml_path) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}


def _copy_shared(dst_base: str, plugin_name: str):
    """Copy _shared.py into the plugin directory at install time.

    Each plugin imports from _shared at runtime. Since Hermes adds only
    the plugin's directory to sys.path, _shared.py must live alongside
    __init__.py inside each installed plugin directory.
    """
    src_base = _get_plugin_dir()
    shared_src = os.path.join(src_base, "_shared.py")
    shared_dst = os.path.join(dst_base, plugin_name, "_shared.py")
    if os.path.exists(shared_src):
        shutil.copy2(shared_src, shared_dst)


def cmd_install_all(args):
    """Install all hermes plugins to H5 profile."""
    src_base = _get_plugin_dir()
    dst_base = _get_target_dir()

    if not os.path.exists(src_base):
        print(f"ERROR: Plugin source not found: {src_base}")
        return 1

    # Collect all plugin directories (ignore _shared.py, __pycache__, etc.)
    plugins = []
    for name in sorted(os.listdir(src_base)):
        src = os.path.join(src_base, name)
        if not os.path.isdir(src) or name.startswith("_"):
            continue
        if os.path.exists(os.path.join(src, "__init__.py")):
            plugins.append(name)

    if not plugins:
        print("No plugins found.")
        return 0

    installed = []
    for name in plugins:
        src = os.path.join(src_base, name)
        dst = os.path.join(dst_base, name)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        _copy_shared(dst_base, name)
        installed.append(name)
        print(f"  ✅ {name} → {dst}")

    print(f"\nInstalled {len(installed)} plugins: {', '.join(installed)}")
    print("Enable each: hermes plugins enable <name>")
    print("Restart Hermes: hermes gateway restart")
    return 0


def cmd_install(args):
    """Install a specific plugin by name."""
    name = args.name
    src_base = _get_plugin_dir()
    dst_base = _get_target_dir()

    # Search for plugin in all subdirectories
    src = None
    for root, dirs, files in os.walk(src_base):
        basename = os.path.basename(root)
        if basename == name and os.path.exists(os.path.join(root, "__init__.py")):
            src = root
            break

    if not src:
        print(f"ERROR: Plugin '{name}' not found in {src_base}")
        print(f"Available: {', '.join(_list_all_plugins(src_base))}")
        return 1

    dst = os.path.join(dst_base, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    _copy_shared(dst_base, name)
    print(f"  ✅ {name} → {dst}")
    print("Enable: hermes plugins enable " + name)
    print("Restart Hermes: hermes gateway restart")
    return 0


def _list_all_plugins(base):
    """List all plugins recursively."""
    result = []
    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name)
        if not os.path.isdir(path) or name.startswith("_"):
            continue
        if os.path.exists(os.path.join(path, "__init__.py")):
            result.append(name)
        else:
            for sub in sorted(os.listdir(path)):
                sub_path = os.path.join(path, sub)
                if os.path.isdir(sub_path) and os.path.exists(os.path.join(sub_path, "__init__.py")):
                    result.append(sub)
    return result


def cmd_list(args):
    """List available hermes plugins."""
    src_base = _get_plugin_dir()
    if not os.path.exists(src_base):
        print("No plugins found.")
        return 0

    plugins = _list_all_plugins(src_base)
    if not plugins:
        print("No plugins found.")
        return 0

    print("Hermes Plugins (available):")
    for name in sorted(set(plugins)):
        # Find the plugin dir
        for root, dirs, files in os.walk(src_base):
            if os.path.basename(root) == name and os.path.exists(os.path.join(root, "__init__.py")):
                meta = _get_plugin_meta(root)
                ver = meta.get("version", "?")
                desc = meta.get("description", "")[:60]
                print(f"  {name} v{ver} — {desc}")
                break
    return 0


def cmd_status(args):
    """Show installed plugin status."""
    dst_base = _get_target_dir()

    if not os.path.exists(dst_base):
        print("Hermes plugins directory not found.")
        return 0

    installed = sorted([
        d for d in os.listdir(dst_base)
        if os.path.isdir(os.path.join(dst_base, d))
        and os.path.exists(os.path.join(dst_base, d, "__init__.py"))
    ])

    if not installed:
        print("No plugins installed. Run: python -m UtilityLib.cli.hermes install-all")
        return 0

    print("Hermes Plugins (installed):")
    for name in installed:
        dst = os.path.join(dst_base, name)
        meta = _get_plugin_meta(dst)
        ver = meta.get("version", "?")
        desc = meta.get("description", "")[:60]
        print(f"  ✅ {name} v{ver} — {desc}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="UtilityLib Hermes Plugin Manager")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install-all", help="Install all hermes plugins")

    install_p = sub.add_parser("install", help="Install a specific plugin")
    install_p.add_argument("name", help="Plugin name")

    sub.add_parser("list", help="List available plugins")
    sub.add_parser("status", help="Show installed plugin status")

    args = parser.parse_args()

    if args.command == "install-all":
        return cmd_install_all(args)
    elif args.command == "install":
        return cmd_install(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "status":
        return cmd_status(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
