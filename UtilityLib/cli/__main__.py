"""
Entry point for UtilityLib CLI tools when invoked as a module.

Usage:
  python -m UtilityLib.cli.git <action> [options]
  python -m UtilityLib.cli.pm2 <action> [options]
  python -m UtilityLib.cli.hermes install-all|install|list|status
"""

import sys

if __name__ == '__main__':
    print("UtilityLib CLI Tools")
    print("\nAvailable tools:")
    print("  python -m UtilityLib.cli.git   - Git automation CLI")
    print("  python -m UtilityLib.cli.pm2   - YAML-driven PM2 process manager")
    print("  python -m UtilityLib.cli.hermes - Hermes plugin manager")
    print("\nUse --help with any tool for more information")
    sys.exit(0)
