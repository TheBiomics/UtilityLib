"""
  GitLib: Git automation utilities for repository management.

  Provides a clean interface for common Git operations including:
  - Repository info and status
  - Clone, pull, push, fetch operations
  - Branch management and switching
  - Pull all branches from remotes
  - Merge checks and conflict detection
  - Commit history and logs
  - Remote management
  - CLI support for automation

  Usage:
    # Single repository
    repo = Git('/path/to/repo')
    repo.pull()
    repo.pull(all_branches=True)  # Pull all branches
    repo.check_if_mergeable('feature-branch', 'main')
    repo.push()

    # Multiple repositories
    mgr = GitManager('/workspace')
    mgr.discover()
    mgr.pull_all_branches_all_repos()
"""

import sys as SYS
import os as OS
import subprocess as SUBPROCESS
from pathlib import Path
from typing import Union, List, Dict, Optional, Any
from .obj import ObjDict
from .path import EntityPath
from .cmd import CMDLib


class Git:
  """
  Represents a Git repository and provides methods for Git operations.

  Usage:
    repo = Git('/path/to/repo')
    repo.status()
    repo.pull()
    repo.pull(all_branches=True)  # Pull all branches
    repo.check_if_mergeable('feature', 'main')
  """

  def __init__(self, path: Union[str, Path, EntityPath] = None):
    """
    Initialize Git repository handler.

    Args:
      path: Path to the Git repository. Defaults to current directory.
    """
    self._path = EntityPath(path or OS.getcwd()).expanduser().resolve()
    self._git_dir = self._path / '.git'

  @property
  def path(self) -> EntityPath:
    """Repository root path."""
    return self._path

  @property
  def exists(self) -> bool:
    """Check if the path is a valid Git repository."""
    return self._git_dir.exists() or self._git_dir.is_file()  # Handle worktrees

  @property
  def name(self) -> str:
    """Repository directory name."""
    return self._path.name

  # ---------------------------------------------------------------------------
  # Core Command Execution
  # ---------------------------------------------------------------------------

  def _run(self, *args, capture: bool = True, check: bool = False, shell: bool = False, **kwargs) -> str:
    """
    Execute a git command in the repository.

    Args:
      *args: Git command arguments (e.g., 'status', '--porcelain')
      capture: Capture stdout (default True)
      check: Raise exception on non-zero exit (default False)
      shell: Use shell mode (default False)
      **kwargs: Additional subprocess.run kwargs

    Returns:
      Command stdout as string, or empty string on error
    """
    if shell:
      cmd = f"git {' '.join(str(a) for a in args)}"
    else:
      cmd = ['git', *[str(a) for a in args]]

    try:
      result = SUBPROCESS.run(
        cmd,
        cwd            = str(self._path),
        capture_output = capture,
        text           = True,
        check          = check,
        shell          = shell,
        **kwargs
      )
      return result.stdout.strip() if result.stdout else ''
    except SUBPROCESS.CalledProcessError as e:
      return e.stderr.strip() if e.stderr else ''
    except Exception:
      return ''

  def _run_safe(self, *args, default: Any = None, **kwargs) -> Any:
    """Run command and return default on any error."""
    try:
      result = self._run(*args, **kwargs)
      return result if result else default
    except Exception:
      return default

  # ---------------------------------------------------------------------------
  # Repository Information
  # ---------------------------------------------------------------------------

  def status(self, short: bool = False) -> str:
    """
    Get repository status.

    Args:
      short: Use short format (--porcelain)

    Returns:
      Status output string
    """
    if short:
      return self._run('status', '--porcelain')
    return self._run('status')

  @property
  def is_clean(self) -> bool:
    """Check if working directory is clean (no uncommitted changes)."""
    return not bool(self.status(short=True))

  @property
  def is_dirty(self) -> bool:
    """Check if working directory has uncommitted changes."""
    return not self.is_clean

  @property
  def current_branch(self) -> str:
    """Get current branch name."""
    return self._run('rev-parse', '--abbrev-ref', 'HEAD')

  @property
  def head_commit(self) -> str:
    """Get HEAD commit hash (short)."""
    return self._run('rev-parse', '--short', 'HEAD')

  @property
  def head_commit_full(self) -> str:
    """Get HEAD commit hash (full)."""
    return self._run('rev-parse', 'HEAD')

  @property
  def root_dir(self) -> EntityPath:
    """Get repository root directory."""
    root = self._run('rev-parse', '--show-toplevel')
    return EntityPath(root) if root else self._path

  # ---------------------------------------------------------------------------
  # Branch Operations
  # ---------------------------------------------------------------------------

  def branches(self, all: bool = False, remote: bool = False) -> List[str]:
    """
    List branches.

    Args:
      all: Include remote branches
      remote: Only remote branches

    Returns:
      List of branch names
    """
    args = ['branch', '--format=%(refname:short)']
    if all:
      args.append('--all')
    elif remote:
      args.append('-r')

    output = self._run(*args)
    branches = [b.strip() for b in output.splitlines() if b.strip()]
    # Filter out HEAD references
    return [b for b in branches if '->' not in b]

  @property
  def local_branches(self) -> List[str]:
    """List local branches."""
    return self.branches()

  @property
  def remote_branches(self) -> List[str]:
    """List remote branches."""
    return self.branches(remote=True)

  @property
  def all_branches(self) -> List[str]:
    """List all branches (local and remote)."""
    return self.branches(all=True)

  def branch_exists(self, branch: str, remote: bool = False) -> bool:
    """Check if a branch exists."""
    branches = self.remote_branches if remote else self.local_branches
    return branch in branches or f'origin/{branch}' in branches

  def checkout(self, branch: str, create: bool = False) -> str:
    """
    Checkout a branch.

    Args:
      branch: Branch name
      create: Create branch if it doesn't exist (-b flag)

    Returns:
      Command output
    """
    if create:
      return self._run('checkout', '-b', branch)
    return self._run('checkout', branch)

  def create_branch(self, branch: str, start_point: str = None) -> str:
    """Create a new branch."""
    args = ['branch', branch]
    if start_point:
      args.append(start_point)
    return self._run(*args)

  def delete_branch(self, branch: str, force: bool = False) -> str:
    """Delete a branch."""
    flag = '-D' if force else '-d'
    return self._run('branch', flag, branch)

  def rename_branch(self, old_name: str, new_name: str) -> str:
    """Rename a branch."""
    return self._run('branch', '-m', old_name, new_name)

  # ---------------------------------------------------------------------------
  # Remote Operations
  # ---------------------------------------------------------------------------

  @property
  def remotes(self) -> List[str]:
    """List remote names."""
    output = self._run('remote')
    return [r.strip() for r in output.splitlines() if r.strip()]

  def remote_url(self, name: str = 'origin') -> str:
    """Get URL for a remote."""
    return self._run('remote', 'get-url', name)

  @property
  def remote_urls(self) -> Dict[str, str]:
    """Get all remote URLs."""
    return {name: self.remote_url(name) for name in self.remotes}

  def set_remote_url(self, url: str, name: str = 'origin') -> str:
    """Set URL for a remote."""
    return self._run('remote', 'set-url', name, url)

  def add_remote(self, name: str, url: str) -> str:
    """Add a new remote."""
    return self._run('remote', 'add', name, url)

  def remove_remote(self, name: str) -> str:
    """Remove a remote."""
    return self._run('remote', 'remove', name)

  # ---------------------------------------------------------------------------
  # Fetch, Pull, Push
  # ---------------------------------------------------------------------------

  def fetch(self, remote: str = None, prune: bool = True, all_remotes: bool = True) -> str:
    """
    Fetch from remote(s).

    Args:
      remote: Specific remote to fetch from
      prune: Remove deleted remote branches (--prune)
      all_remotes: Fetch from all remotes (--all)

    Returns:
      Command output
    """
    args = ['fetch']
    if all_remotes and not remote:
      args.append('--all')
    elif remote:
      args.append(remote)
    if prune:
      args.append('--prune')
    return self._run(*args)

  def pull(self, remote: str = 'origin', branch: str = None, rebase: bool = False,
           all_branches: bool = False) -> Union[str, List[Dict[str, str]]]:
    """
    Pull from remote.

    Args:
      remote: Remote name
      branch: Branch to pull (defaults to current, ignored if all_branches=True)
      rebase: Use rebase instead of merge
      all_branches: If True, pull all remote branches. If False, pull only specified/current branch

    Returns:
      - If all_branches=False: Command output string
      - If all_branches=True: List of dicts with branch name and pull result

    Examples:
      # Pull current branch
      repo.pull()

      # Pull specific branch
      repo.pull(branch='main')

      # Pull all branches
      repo.pull(all_branches=True)
    """
    if all_branches:
      return self._pull_all_branches_impl(remote)

    # Single branch pull
    args = ['pull']
    if rebase:
      args.append('--rebase')
    args.append(remote)
    if branch:
      args.append(branch)
    return self._run(*args)

  def _pull_all_branches_impl(self, remote: str = 'origin') -> List[Dict[str, str]]:
    """
    Internal implementation for pulling all remote branches.

    This method:
    1. Fetches all remote branches
    2. Creates local tracking branches for each
    3. Pulls updates for each branch
    4. Restores the original branch

    Args:
      remote: Remote name (default: origin)

    Returns:
      List of dicts with branch name and pull result
    """
    results = []

    # Save current branch
    original_branch = self.current_branch

    # Fetch all
    fetch_result = self.fetch(all_remotes=True, prune=True)
    results.append({'branch': '_fetch', 'result': fetch_result, 'status': 'ok'})

    # Get remote branches
    remote_branches = self.remote_branches

    for remote_branch in remote_branches:
      # Extract local branch name (remove origin/ prefix)
      if '/' in remote_branch:
        local_branch = remote_branch.split('/', 1)[1]
      else:
        local_branch = remote_branch

      # Skip HEAD
      if local_branch == 'HEAD':
        continue

      try:
        # Create tracking branch if doesn't exist
        if not self.branch_exists(local_branch):
          self._run('branch', '--track', local_branch, remote_branch)

        # Checkout and pull
        checkout_res = self.checkout(local_branch)
        pull_res = self.pull(remote, local_branch)

        results.append({
          'branch': local_branch,
          'result': pull_res or checkout_res,
          'status': 'ok'
        })
      except Exception as e:
        results.append({
          'branch': local_branch,
          'result': str(e),
          'status': 'error'
        })

    # Restore original branch
    self.checkout(original_branch)

    return results


  def push(self, remote: str = 'origin', branch: str = None,
           force: bool = False, set_upstream: bool = False, tags: bool = False) -> str:
    """
    Push to remote.

    Args:
      remote: Remote name
      branch: Branch to push (defaults to current)
      force: Force push
      set_upstream: Set upstream tracking
      tags: Push tags

    Returns:
      Command output
    """
    args = ['push']
    if force:
      args.append('--force')
    if set_upstream:
      args.append('--set-upstream')
    if tags:
      args.append('--tags')
    args.append(remote)
    if branch:
      args.append(branch)
    return self._run(*args)

  # ---------------------------------------------------------------------------
  # Commit Operations
  # ---------------------------------------------------------------------------

  def add(self, *files, all: bool = False) -> str:
    """
    Stage files for commit.

    Args:
      *files: Files to add
      all: Add all changes (-A)

    Returns:
      Command output
    """
    if all:
      return self._run('add', '-A')
    return self._run('add', *files)

  def commit(self, message: str, all: bool = False, amend: bool = False) -> str:
    """
    Create a commit.

    Args:
      message: Commit message
      all: Stage all tracked files (-a)
      amend: Amend previous commit

    Returns:
      Command output
    """
    args = ['commit', '-m', message]
    if all:
      args.insert(1, '-a')
    if amend:
      args.append('--amend')
    return self._run(*args)

  def reset(self, ref: str = 'HEAD', mode: str = 'mixed', files: List[str] = None) -> str:
    """
    Reset HEAD to a state.

    Args:
      ref: Reference to reset to
      mode: Reset mode (soft, mixed, hard)
      files: Specific files to reset

    Returns:
      Command output
    """
    args = ['reset', f'--{mode}', ref]
    if files:
      args.extend(files)
    return self._run(*args)

  def stash(self, message: str = None, include_untracked: bool = False) -> str:
    """Stash changes."""
    args = ['stash', 'push']
    if message:
      args.extend(['-m', message])
    if include_untracked:
      args.append('-u')
    return self._run(*args)

  def stash_pop(self, index: int = 0) -> str:
    """Pop stash."""
    return self._run('stash', 'pop', f'stash@{{{index}}}')

  @property
  def stash_list(self) -> List[str]:
    """List stashes."""
    output = self._run('stash', 'list')
    return output.splitlines() if output else []

  # ---------------------------------------------------------------------------
  # Log and History
  # ---------------------------------------------------------------------------

  def log(self, n: int = 10, oneline: bool = True, branch: str = None,
          format: str = None, since: str = None, until: str = None) -> List[str]:
    """
    Get commit log.

    Args:
      n: Number of commits
      oneline: One line per commit
      branch: Specific branch
      format: Custom format string
      since: Start date
      until: End date

    Returns:
      List of log entries
    """
    args = ['log', f'-{n}']
    if oneline and not format:
      args.append('--oneline')
    if format:
      args.append(f'--pretty=format:{format}')
    if since:
      args.append(f'--since={since}')
    if until:
      args.append(f'--until={until}')
    if branch:
      args.append(branch)

    output = self._run(*args)
    return output.splitlines() if output else []

  def first_commit_date(self, branch: str = None) -> str:
    """Get date of first commit on branch."""
    args = ['log', '--reverse', '--pretty=format:%ad', '--date=short', '-1']
    if branch:
      args.append(branch)
    return self._run(*args)

  def last_commit_date(self, branch: str = None) -> str:
    """Get date of last commit on branch."""
    args = ['log', '--pretty=format:%ad', '--date=short', '-1']
    if branch:
      args.append(branch)
    return self._run(*args)

  def show(self, ref: str = 'HEAD', stat: bool = False) -> str:
    """Show commit details."""
    args = ['show', ref]
    if stat:
      args.append('--stat')
    return self._run(*args)

  def blame(self, file: str, line_range: tuple = None) -> str:
    """
    Show file blame/annotation.

    Args:
      file: File to blame
      line_range: Optional (start, end) line range

    Returns:
      Blame output
    """
    args = ['blame', file]
    if line_range:
      args.extend(['-L', f'{line_range[0]},{line_range[1]}'])
    return self._run(*args)

  def diff(self, ref1: str = None, ref2: str = None, files: List[str] = None,
           stat: bool = False, name_only: bool = False) -> str:
    """
    Show diff.

    Args:
      ref1: First reference
      ref2: Second reference
      files: Specific files
      stat: Show stat instead of full diff
      name_only: Only show changed file names

    Returns:
      Diff output
    """
    args = ['diff']
    if stat:
      args.append('--stat')
    if name_only:
      args.append('--name-only')
    if ref1:
      args.append(ref1)
    if ref2:
      args.append(ref2)
    if files:
      args.append('--')
      args.extend(files)
    return self._run(*args)

  def changed_files(self, ref1: str = 'HEAD~1', ref2: str = 'HEAD') -> List[str]:
    """Get list of changed files between refs."""
    output = self.diff(ref1, ref2, name_only=True)
    return output.splitlines() if output else []

  # ---------------------------------------------------------------------------
  # Merge Operations
  # ---------------------------------------------------------------------------

  def merge(self, branch: str, no_ff: bool = False, squash: bool = False,
            message: str = None, abort: bool = False) -> str:
    """
    Merge a branch.

    Args:
      branch: Branch to merge
      no_ff: Create merge commit even for fast-forward
      squash: Squash commits
      message: Merge commit message
      abort: Abort ongoing merge

    Returns:
      Command output
    """
    if abort:
      return self._run('merge', '--abort')

    args = ['merge', branch]
    if no_ff:
      args.append('--no-ff')
    if squash:
      args.append('--squash')
    if message:
      args.extend(['-m', message])
    return self._run(*args)

  def is_merged(self, branch: str, into: str = 'master') -> bool:
    """Check if branch is merged into target."""
    merged = self._run('branch', '--merged', into)
    return branch in merged.split()

  def can_merge(self, branch: str, into: str = None) -> bool:
    """
    Check if branch can be merged without conflicts.

    Args:
      branch: Source branch
      into: Target branch (default: current)

    Returns:
      True if mergeable without conflicts
    """
    into = into or self.current_branch
    # Get merge base
    base = self._run('merge-base', into, branch)
    if not base:
      return False

    # Try merge-tree to detect conflicts
    result = self._run('merge-tree', base, into, branch)
    return '<<<<<<<' not in result

  def check_if_mergeable(self, branch1: str, branch2: str = None) -> Union[bool, Dict[str, bool]]:
    """
    Check if branches can be merged without conflicts.

    Args:
      branch1: First branch to check
      branch2: Second branch to compare with. If None, compares branch1 with all other branches

    Returns:
      - If branch2 specified: bool indicating if mergeable
      - If branch2 is None: dict mapping branch names to mergeable status

    Examples:
      # Check if feature can merge into main
      repo.check_if_mergeable('feature', 'main')  # -> True/False

      # Check feature against all branches
      repo.check_if_mergeable('feature')  # -> {'main': True, 'develop': False, ...}
    """
    if branch2:
      # Single comparison
      return self.can_merge(branch1, branch2)

    # Compare against all branches
    all_branches = [b for b in self.local_branches if b != branch1]
    results = {}

    for target_branch in all_branches:
      try:
        results[target_branch] = self.can_merge(branch1, target_branch)
      except Exception:
        results[target_branch] = None

    return results

  def merge_base(self, branch1: str, branch2: str) -> str:
    """Get common ancestor of two branches."""
    return self._run('merge-base', branch1, branch2)

  def rebase(self, onto: str = None, interactive: bool = False, abort: bool = False) -> str:
    """Rebase current branch."""
    if abort:
      return self._run('rebase', '--abort')

    args = ['rebase']
    if interactive:
      args.append('-i')
    if onto:
      args.append(onto)
    return self._run(*args)

  # ---------------------------------------------------------------------------
  # Tags
  # ---------------------------------------------------------------------------

  @property
  def tags(self) -> List[str]:
    """List tags."""
    output = self._run('tag', '-l')
    return output.splitlines() if output else []

  def create_tag(self, name: str, message: str = None, ref: str = None) -> str:
    """Create a tag."""
    args = ['tag']
    if message:
      args.extend(['-a', name, '-m', message])
    else:
      args.append(name)
    if ref:
      args.append(ref)
    return self._run(*args)

  def delete_tag(self, name: str, remote: bool = False) -> str:
    """Delete a tag."""
    if remote:
      return self._run('push', 'origin', f':refs/tags/{name}')
    return self._run('tag', '-d', name)

  # ---------------------------------------------------------------------------
  # Configuration
  # ---------------------------------------------------------------------------

  def config_get(self, key: str, scope: str = None) -> str:
    """
    Get config value.

    Args:
      key: Config key
      scope: Config scope (local, global, system)
    """
    args = ['config']
    if scope:
      args.append(f'--{scope}')
    args.append('--get')
    args.append(key)
    return self._run(*args)

  def config_set(self, key: str, value: str, scope: str = 'local') -> str:
    """
    Set config value.

    Args:
      key: Config key
      value: Config value
      scope: Config scope (local, global, system)
    """
    return self._run('config', f'--{scope}', key, value)

  def config_list(self, scope: str = None) -> Dict[str, str]:
    """List all config values."""
    args = ['config', '--list']
    if scope:
      args.append(f'--{scope}')
    output = self._run(*args)
    config = {}
    for line in output.splitlines():
      if '=' in line:
        key, value = line.split('=', 1)
        config[key] = value
    return config

  @property
  def user_name(self) -> str:
    """Get configured user name."""
    return self.config_get('user.name')

  @property
  def user_email(self) -> str:
    """Get configured user email."""
    return self.config_get('user.email')

  # ---------------------------------------------------------------------------
  # Branch Details / Analysis
  # ---------------------------------------------------------------------------

  def branch_details(self, main_branch: str = 'master') -> List[Dict]:
    """
    Get detailed info about all branches.

    Args:
      main_branch: Main branch to check merge status against

    Returns:
      List of branch detail dicts
    """
    details = []
    for branch in self.all_branches:
      # Skip HEAD pointer
      if '->' in branch:
        continue

      info = {
        'repo': self.name,
        'branch': branch,
        'first_commit': self.first_commit_date(branch),
        'last_commit': self.last_commit_date(branch),
        'is_merged': self.is_merged(branch.replace('origin/', ''), main_branch),
        'mergeable': self.can_merge(branch, main_branch) if not self.is_merged(branch.replace('origin/', ''), main_branch) else None
      }
      details.append(info)
    return details

  # ---------------------------------------------------------------------------
  # Clone Operations (Static)
  # ---------------------------------------------------------------------------

  @staticmethod
  def clone(url: str, path: str = None, branch: str = None,
            depth: int = None, bare: bool = False) -> 'Git':
    """
    Clone a repository.

    Args:
      url: Repository URL
      path: Destination path
      branch: Specific branch to clone
      depth: Shallow clone depth
      bare: Create bare repository

    Returns:
      Git instance for cloned repository
    """
    args = ['git', 'clone']
    if branch:
      args.extend(['-b', branch])
    if depth:
      args.extend(['--depth', str(depth)])
    if bare:
      args.append('--bare')
    args.append(url)
    if path:
      args.append(path)

    SUBPROCESS.run(args, check=True, capture_output=True, text=True)

    # Determine repo path
    if path:
      repo_path = path
    else:
      # Extract from URL
      repo_path = url.rstrip('/').split('/')[-1].replace('.git', '')

    return Git(repo_path)

  # ---------------------------------------------------------------------------
  # Utility Methods
  # ---------------------------------------------------------------------------

  def clean(self, directories: bool = False, force: bool = False,
            dry_run: bool = True, ignored: bool = False) -> str:
    """
    Clean untracked files.

    Args:
      directories: Remove directories too
      force: Actually remove (required unless dry_run)
      dry_run: Only show what would be removed
      ignored: Remove ignored files too

    Returns:
      Command output
    """
    args = ['clean']
    if dry_run:
      args.append('-n')
    elif force:
      args.append('-f')
    if directories:
      args.append('-d')
    if ignored:
      args.append('-x')
    return self._run(*args)

  def gc(self, aggressive: bool = False, prune: str = 'now') -> str:
    """Run garbage collection."""
    args = ['gc']
    if aggressive:
      args.append('--aggressive')
    if prune:
      args.append(f'--prune={prune}')
    return self._run(*args)

  def archive(self, output: str, ref: str = 'HEAD', format: str = 'zip') -> str:
    """Create archive of repository."""
    return self._run('archive', f'--format={format}', f'--output={output}', ref)

  def __repr__(self) -> str:
    return f"GitRepo('{self._path}')"

  def __str__(self) -> str:
    return f"Git: {self.name} @ {self.current_branch}"


class GitManager:
  """
  Manage multiple Git repositories.

  Usage:
    mgr = GitManager('/path/to/workspace')
    mgr.discover()
    mgr.fetch_all()
    mgr.pull_all_branches_all_repos()
  """

  def __init__(self, workspace: Union[str, Path, EntityPath] = None):
    """
    Initialize GitManager.

    Args:
      workspace: Workspace root path
    """
    self._workspace = EntityPath(workspace or OS.getcwd()).resolved()
    self._repos: List[Git] = []

  @property
  def workspace(self) -> EntityPath:
    return self._workspace

  @property
  def repos(self) -> List[Git]:
    return self._repos

  def discover(self, depth: int = 2) -> List[Git]:
    """
    Discover Git repositories in workspace.

    Args:
      depth: How deep to search for .git directories

    Returns:
      List of discovered Git instances
    """
    self._repos = []
    pattern = '/'.join(['*'] * depth) + '/.git'

    for git_dir in self._workspace.glob(pattern):
      if git_dir.is_dir() or git_dir.is_file():  # Handle worktrees
        parent = git_dir.parent() if callable(git_dir.parent) else git_dir.parent
        repo = Git(parent)
        self._repos.append(repo)

    return self._repos

  def add_repo(self, path: Union[str, Path, Git]) -> Git:
    """Add a repository to manage."""
    if isinstance(path, Git):
      repo = path
    else:
      repo = Git(path)

    if repo.exists and repo not in self._repos:
      self._repos.append(repo)
    return repo

  def add_repos_from_file(self, file_path: Union[str, Path]) -> List[Git]:
    """
    Add repositories from a text file (one repo name per line).

    Args:
      file_path: Path to file containing repo names

    Returns:
      List of added repos
    """
    file_path = EntityPath(file_path)
    if not file_path.exists():
      return []

    added = []
    for line in file_path.read_text().splitlines():
      repo_name = line.strip()
      if repo_name and not repo_name.startswith('#'):
        repo = self.add_repo(self._workspace / repo_name)
        if repo:
          added.append(repo)
    return added

  def fetch_all(self, prune: bool = True) -> Dict[str, str]:
    """Fetch all repositories."""
    results = {}
    for repo in self._repos:
      results[repo.name] = repo.fetch(prune=prune)
    return results

  def pull_all(self, rebase: bool = False) -> Dict[str, str]:
    """Pull all repositories (current branch only)."""
    results = {}
    for repo in self._repos:
      results[repo.name] = repo.pull(rebase=rebase)
    return results

  def pull_all_branches_all_repos(self) -> Dict[str, List[Dict]]:
    """
    Pull all branches for all repositories.

    Returns:
      Dict mapping repo name to list of branch pull results
    """
    results = {}
    for repo in self._repos:
      print(f"Processing: {repo.name}")
      results[repo.name] = repo.pull_all_branches()
    return results

  def status_all(self, short: bool = True) -> Dict[str, str]:
    """Get status of all repositories."""
    results = {}
    for repo in self._repos:
      status = repo.status(short=short)
      results[repo.name] = status if status else 'clean'
    return results

  def clone_repos(self, urls: List[str], base_url: str = None) -> List[Git]:
    """
    Clone multiple repositories.

    Args:
      urls: List of URLs or repo names
      base_url: Base URL to prepend to names (e.g., git@github.com:user/)

    Returns:
      List of cloned Git instances
    """
    cloned = []
    for url in urls:
      if base_url and not url.startswith(('http', 'git@', 'ssh://')):
        url = f"{base_url.rstrip('/')}/{url}"

      try:
        repo = Git.clone(url, path=str(self._workspace / url.split('/')[-1].replace('.git', '')))
        self._repos.append(repo)
        cloned.append(repo)
      except Exception as e:
        print(f"Failed to clone {url}: {e}")

    return cloned

  def summary(self) -> List[Dict]:
    """Get summary of all repositories."""
    summaries = []
    for repo in self._repos:
      summaries.append({
        'name': repo.name,
        'path': str(repo.path),
        'branch': repo.current_branch,
        'clean': repo.is_clean,
        'remotes': repo.remotes,
      })
    return summaries

  def list_all_repos(self, detailed: bool = False) -> List[Union[str, Dict]]:
    """
    List all managed repositories.

    Args:
      detailed: If True, return detailed info dict. If False, return just names.

    Returns:
      List of repo names or detailed repo information

    Example:
      mgr = GitManager('~/workspace')
      mgr.discover()

      # Simple list
      names = mgr.list_all_repos()  # ['repo1', 'repo2', ...]

      # Detailed list
      details = mgr.list_all_repos(detailed=True)
      # [{'name': 'repo1', 'branch': 'main', ...}, ...]
    """
    if detailed:
      return self.summary()
    return [repo.name for repo in self._repos]

  def print_repos(self, show_status: bool = True, show_remotes: bool = False) -> None:
    """
    Pretty print all managed repositories.

    Args:
      show_status: Show clean/dirty status
      show_remotes: Show remote URLs

    Example:
      mgr = GitManager('~/workspace')
      mgr.discover()
      mgr.print_repos(show_status=True, show_remotes=True)
    """
    if not self._repos:
      print("No repositories managed.")
      return

    print(f"\n{'='*70}")
    print(f"Workspace: {self._workspace}")
    print(f"Total Repositories: {len(self._repos)}")
    print(f"{'='*70}\n")

    for i, repo in enumerate(self._repos, 1):
      status_icon = '✓' if repo.is_clean else '✗'
      status_text = 'clean' if repo.is_clean else 'dirty'

      print(f"{i:3d}. {repo.name}")
      print(f"     Path:   {repo.path}")
      print(f"     Branch: {repo.current_branch}")

      if show_status:
        print(f"     Status: {status_icon} {status_text}")

      if show_remotes:
        remotes = repo.remotes
        if remotes:
          for remote in remotes:
            url = repo.remote_url(remote)
            print(f"     Remote: {remote} → {url}")
        else:
          print(f"     Remote: (none)")

      print()

  def list_by_status(self, dirty_only: bool = False, clean_only: bool = False) -> List[Git]:
    """
    Filter repositories by status.

    Args:
      dirty_only: Return only dirty repos (uncommitted changes)
      clean_only: Return only clean repos

    Returns:
      Filtered list of Git instances
    """
    if dirty_only:
      return [repo for repo in self._repos if repo.is_dirty]
    elif clean_only:
      return [repo for repo in self._repos if repo.is_clean]
    return self._repos

  def list_by_branch(self, branch: str) -> List[Git]:
    """
    Filter repositories by current branch.

    Args:
      branch: Branch name to filter by

    Returns:
      List of repos on the specified branch
    """
    return [repo for repo in self._repos if repo.current_branch == branch]

  def __len__(self) -> int:
    return len(self._repos)

  def __iter__(self):
    return iter(self._repos)

  def __getitem__(self, key: Union[int, str]) -> Git:
    if isinstance(key, int):
      return self._repos[key]
    for repo in self._repos:
      if repo.name == key:
        return repo
    raise KeyError(f"Repository '{key}' not found")


# Backward compatibility alias
GitRepo = Git


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------
# CLI interface has been moved to UtilityLib.cli.git
# Usage: python -m UtilityLib.cli.git <action> [options]
# See: UtilityLib/cli/git.py
