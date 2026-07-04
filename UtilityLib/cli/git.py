#!/usr/bin/env python3
"""
Git CLI - Command-line interface for Git automation

Usage:
  python -m UtilityLib.cli.git <action> [options]

Actions:
  status      - Show repository status
  pull        - Pull from remote
  push        - Push to remote
  fetch       - Fetch from remote
  branches    - List branches
  mergeable   - Check merge compatibility
  clone       - Clone repository
  log         - Show commit log

Examples:
  # Show status
  python -m UtilityLib.cli.git status --path /path/to/repo

  # Pull all branches
  python -m UtilityLib.cli.git pull --all-branches

  # Check mergeability
  python -m UtilityLib.cli.git mergeable --branch feature --branch2 main

  # Clone repository
  python -m UtilityLib.cli.git clone --url https://github.com/user/repo.git
"""

import sys as SYS
from ..lib.git import Git
from ..lib.cmd import CMDLib


def main():
  """Command-line interface for Git operations."""
  parser = CMDLib.init_cli(version='UtilityLib.Git v1.0', description='Git automation CLI')

  parser.add_argument('action',
                     choices=['status', 'pull', 'push', 'fetch', 'branches',
                             'mergeable', 'clone', 'log'],
                     help='Git action to perform')

  parser.add_argument('--path', '-p', default='.',
                     help='Repository path (default: current directory)')

  parser.add_argument('--branch', '-b',
                     help='Branch name')

  parser.add_argument('--branch2',
                     help='Second branch for comparison')

  parser.add_argument('--remote', '-r', default='origin',
                     help='Remote name (default: origin)')

  parser.add_argument('--url', '-u',
                     help='Repository URL for clone')

  parser.add_argument('--force', '-f', action='store_true',
                     help='Force operation')

  parser.add_argument('--all', '-a', action='store_true',
                     help='Apply to all branches/remotes')

  parser.add_argument('--all-branches', action='store_true',
                     help='Pull all branches (for pull action)')

  args = parser.parse_args()

  # Initialize repository
  if args.action == 'clone':
    if not args.url:
      print("Error: --url required for clone action")
      SYS.exit(1)
    repo = Git.clone(args.url, args.path)
    print(f"Cloned to: {repo.path}")
    return

  repo = Git(args.path)

  if not repo.exists:
    print(f"Error: Not a git repository: {args.path}")
    SYS.exit(1)

  # Execute action
  if args.action == 'status':
    print(repo.status())

  elif args.action == 'pull':
    # Check for all_branches flag (either --all or --all-branches)
    all_branches = getattr(args, 'all_branches', False) or args.all

    if all_branches:
      results = repo.pull(all_branches=True)
      for r in results:
        print(f"{r['branch']}: {r['status']}")
    else:
      result = repo.pull(args.remote, args.branch)
      print(result)

  elif args.action == 'push':
    result = repo.push(args.remote, args.branch, force=args.force)
    print(result)

  elif args.action == 'fetch':
    result = repo.fetch(args.remote if not args.all else None)
    print(result)

  elif args.action == 'branches':
    branches = repo.all_branches() if args.all else repo.local_branches()
    for branch in branches:
      print(branch)

  elif args.action == 'mergeable':
    if not args.branch:
      print("Error: --branch required for mergeable check")
      SYS.exit(1)

    result = repo.check_if_mergeable(args.branch, args.branch2)

    if isinstance(result, dict):
      print(f"Mergeability of '{args.branch}' into other branches:")
      for target, status in result.items():
        status_str = '✓' if status else '✗' if status is False else '?'
        print(f"  {status_str} {target}")
    else:
      status = '✓ Can merge' if result else '✗ Conflicts detected'
      print(f"{args.branch} -> {args.branch2}: {status}")

  elif args.action == 'log':
    n = 10 if not args.all else 50
    logs = repo.log(n=n)
    for log_entry in logs:
      print(log_entry)


if __name__ == '__main__':
  main()
