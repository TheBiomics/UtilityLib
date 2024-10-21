Help on class EntityPath in module UtilityLib.lib.entity:

# class EntityPath(pathlib.Path)

    EntityPath(*args, **kwargs)

    A versatile extension of Python's built-in `Path` class to simplify and enhance file and directory handling.

    Key Features:
    --------------
    1. **Extended Operators**: Implements custom operators (`//`, `%`, `-`, `+`) for intuitive path manipulation.
        - `//` (Floor division): Splits the path into segments based on integer or string input.
        - `%` (Modulo): Allows dynamic string formatting within paths.
        - `-` (Subtraction): Removes segments from the path, either by an index or up to a matching string.
        - `+` (Addition): Concatenates new path components easily.

    2. **Search and Match**: Provides methods for pattern matching and file type identification.
        - Methods like `search`, `has`, and `get_match` allow users to quickly find files or directories using flexible patterns.

    3. **File and Directory Operations**: Simplifies common filesystem tasks like reading, writing, moving, copying, and deleting files or directories.
        - Methods for safely deleting files (`delete` with `force_delete`).
        - List all files, directories, or both using `list_files`, `list_dirs`, or `list_items`.
        - Quick read/write utilities like `read_text`, `write_text`, `head`, and `tail` for file content manipulation.

    4. **Metadata and Stats**: Efficiently retrieve file or directory metadata.
        - Properties like `size`, `permission`, `created`, `updated`, and `hash` provide quick access to key attributes.
        - Comprehensive stat retrieval via `stats` for access, modification, and creation times.

    5. **Compression Detection**: Automatically detect if a file is compressed, based on file extension (`is_gz`).

    6. **Path Formatting**: Methods like `rel_path`, `parent`, and `full_path` make it easy to convert paths to relative, parent, or absolute forms.

    Additional Utilities:
    ---------------------
    - `validate`: Creates the file or directory if it doesn't exist.
    - `move` and `copy`: Move or copy files and directories to new locations with automatic parent directory creation if necessary.
    - `get_hash`: Calculate file or directory hash using common algorithms like `sha256` and `md5` for integrity checks.

    This class is designed to make filesystem operations more intuitive and reduce repetitive boilerplate code, improving readability and efficiency in path manipulation tasks.

    Method resolution order:
        EntityPath
        pathlib.Path
        pathlib.PurePath
        builtins.object

    Methods defined here:

    __add__(self, what='')

    __floordiv__(self, what)
        Flood Division (// operator) to return based on str or int

    __len__ = len(self)

    __mod__(self, what='')
        Modulo operand operation on EntityPath

    __str__(self)
        Return the string representation of the path, suitable for
        passing to system calls.

    __sub__(self, what)
        Subtraction operator (-) for removing segments from a path.

    contains = has(self, file=None)

    copy(self, destination)
        Copy the file or directory to a new location.

    delete(self, force_delete=None)

    exists(self)
        Check if the path exists.

    ext_type = search(self, pattern='**')

    file_type = search(self, pattern='**')

    folders = list_dirs(self)

    get_hash(self, algorithm='sha256')
        Compute the hash of the file or directory using the specified algorithm.

        :param algorithm: Hash algorithm to use ('md5', 'sha256', etc.)
        :return: The computed hash as a hexadecimal string

    get_match(self, pattern='*txt')

    get_name(self)
        Return the name of the file or directory.

    get_size(self, converter=None)
        Return the size of the file or directory.

    get_stats(self)

    get_stem(self)
        Return the stem of the file or directory (filename without extension).

    has(self, file=None)
        Case sensitive check if pattern (e.g., **/file.txt; *ile.tx*) exists

    has_dir = has(self, file=None)

    has_file = has(self, file=None)

    head(self, lines=1)
        Return first few lines of a file

    help(self)
        Extension(s): Path.suffix, Path.suffixes
        Name: Path.name
        Stem: Path.stem (without suffixes)

        ## Noteable Methods
        Path.rglob(pattern, *, case_sensitive=None)
        Path.samefile(other_path)
        Path.symlink_to(target, target_is_directory=False)
        Path.write_bytes(data) # Write binary data
        Path.walk()
        Path.rename(target)
        Path.replace(target)
        Path.expanduser()
        Path.exists(*, follow_symlinks=True)
        Path.chmod(mode, *, follow_symlinks=True)
        Path.cwd()
        Path.with_name(new_name.ext) # Replaces the file name
        Path.with_stem(new_name) # Changes the file name (keeping extension)
        Path.with_suffix
        Path.match
        Path.parts

    len(self)

    list_dirs(self)
        List all directories in the directory.

    list_files(self, relative=True)
        List all files in the directory.

    list_items(self)
        List all items (files and directories) in the directory.

    lower(self)

    move(self, destination)
        Move the file or directory to a new location.

    parent(self, level=0)
        Return the parent directory.

    read = _read_file(self, method=None)

    read_lines = _read_lines(self, num_lines=None)

    read_text = _read_file(self, method=None)

    readline = _read_lines(self, num_lines=None)

    readlines = _read_lines(self, num_lines=None)

    rel_path(self, _path=None)
        Return the relative path from the current working directory.

    search(self, pattern='**')

    tail(self, lines=1, buffer_size=4098)
        Tail a file and get X lines from the end
        Source: https://stackoverflow.com/a/13790289

    type_ext = search(self, pattern='**')

    upper(self)

    validate(self)
        Make directory/file if doesn't exist.

    write = write_text(self, data, mode='a')

    write_text(self, data, mode='a')
        Write the given text to the file.

    ----------------------------------------------------------------------
    Static methods defined here:

    __new__(self, *args, **kwargs)
        Construct a PurePath from one or several strings and or existing
        PurePath objects.  The strings and path objects are combined so as
        to yield a canonicalized path, which is incorporated into the
        new PurePath object.

    ----------------------------------------------------------------------
    Readonly properties defined here:

    accessed

    created

    dirs

    entities

    ext

    files

    full_path
        Return the absolute path.

    hash

    is_compressed

    is_gz

    items

    mode

    modified

    permission

    size

    stats

    text

    updated

    ----------------------------------------------------------------------
    Data descriptors defined here:

    __dict__
        dictionary for instance variables (if defined)

    __weakref__
        list of weak references to the object (if defined)

    ----------------------------------------------------------------------
    Data and other attributes defined here:

    force_delete = False

    ----------------------------------------------------------------------
    Methods inherited from pathlib.Path:

    __enter__(self)

    __exit__(self, t, v, tb)

    absolute(self)
        Return an absolute version of this path.  This function works
        even if the path doesn't point to anything.

        No normalization is done, i.e. all '.' and '..' will be kept along.
        Use resolve() to get the canonical path to a file.

    chmod(self, mode)
        Change the permissions of the path, like os.chmod().

    expanduser(self)
        Return a new path with expanded ~ and ~user constructs
        (as returned by os.path.expanduser)

    glob(self, pattern)
        Iterate over this subtree and yield all existing files (of any
        kind, including directories) matching the given relative pattern.

    group(self)
        Return the group name of the file gid.

    is_block_device(self)
        Whether this path is a block device.

    is_char_device(self)
        Whether this path is a character device.

    is_dir(self)
        Whether this path is a directory.

    is_fifo(self)
        Whether this path is a FIFO.

    is_file(self)
        Whether this path is a regular file (also True for symlinks pointing
        to regular files).

    is_mount(self)
        Check if this path is a POSIX mount point

    is_socket(self)
        Whether this path is a socket.

    is_symlink(self)
        Whether this path is a symbolic link.

    iterdir(self)
        Iterate over the files in this directory.  Does not yield any
        result for the special paths '.' and '..'.

    lchmod(self, mode)
        Like chmod(), except if the path points to a symlink, the symlink's
        permissions are changed, rather than its target's.

    link_to(self, target)
        Make the target path a hard link pointing to this path.

        Note this function does not make this path a hard link to *target*,
        despite the implication of the function and argument names. The order
        of arguments (target, link) is the reverse of Path.symlink_to, but
        matches that of os.link.

    lstat(self)
        Like stat(), except if the path points to a symlink, the symlink's
        status information is returned, rather than its target's.

    mkdir(self, mode=511, parents=False, exist_ok=False)
        Create a new directory at this given path.

    open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None)
        Open the file pointed by this path and return a file object, as
        the built-in open() function does.

    owner(self)
        Return the login name of the file owner.

    read_bytes(self)
        Open the file in bytes mode, read it, and close the file.

    rename(self, target)
        Rename this path to the target path.

        The target path may be absolute or relative. Relative paths are
        interpreted relative to the current working directory, *not* the
        directory of the Path object.

        Returns the new Path instance pointing to the target path.

    replace(self, target)
        Rename this path to the target path, overwriting if that path exists.

        The target path may be absolute or relative. Relative paths are
        interpreted relative to the current working directory, *not* the
        directory of the Path object.

        Returns the new Path instance pointing to the target path.

    resolve(self, strict=False)
        Make the path absolute, resolving all symlinks on the way and also
        normalizing it (for example turning slashes into backslashes under
        Windows).

    rglob(self, pattern)
        Recursively yield all existing files (of any kind, including
        directories) matching the given relative pattern, anywhere in
        this subtree.

    rmdir(self)
        Remove this directory.  The directory must be empty.

    samefile(self, other_path)
        Return whether other_path is the same or not as this file
        (as returned by os.path.samefile()).

    stat(self)
        Return the result of the stat() system call on this path, like
        os.stat() does.

    symlink_to(self, target, target_is_directory=False)
        Make this path a symlink pointing to the target path.
        Note the order of arguments (link, target) is the reverse of os.symlink.

    touch(self, mode=438, exist_ok=True)
        Create this file with the given access mode, if it doesn't exist.

    unlink(self, missing_ok=False)
        Remove this file or link.
        If the path is a directory, use rmdir() instead.

    write_bytes(self, data)
        Open the file in bytes mode, write to it, and close the file.

    ----------------------------------------------------------------------
    Class methods inherited from pathlib.Path:

    cwd() from builtins.type
        Return a new path pointing to the current working directory
        (as returned by os.getcwd()).

    home() from builtins.type
        Return a new path pointing to the user's home directory (as
        returned by os.path.expanduser('~')).

    ----------------------------------------------------------------------
    Methods inherited from pathlib.PurePath:

    __bytes__(self)
        Return the bytes representation of the path.  This is only
        recommended to use under Unix.

    __eq__(self, other)
        Return self==value.

    __fspath__(self)

    __ge__(self, other)
        Return self>=value.

    __gt__(self, other)
        Return self>value.

    __hash__(self)
        Return hash(self).

    __le__(self, other)
        Return self<=value.

    __lt__(self, other)
        Return self<value.

    __reduce__(self)
        Helper for pickle.

    __repr__(self)
        Return repr(self).

    __rtruediv__(self, key)

    __truediv__(self, key)

    as_posix(self)
        Return the string representation of the path with forward (/)
        slashes.

    as_uri(self)
        Return the path as a 'file' URI.

    is_absolute(self)
        True if the path is absolute (has both a root and, if applicable,
        a drive).

    is_reserved(self)
        Return True if the path contains one of the special names reserved
        by the system, if any.

    joinpath(self, *args)
        Combine this path with one or several arguments, and return a
        new path representing either a subpath (if all arguments are relative
        paths) or a totally different path (if one of the arguments is
        anchored).

    match(self, path_pattern)
        Return True if this path matches the given pattern.

    relative_to(self, *other)
        Return the relative path to another path identified by the passed
        arguments.  If the operation is not possible (because this is not
        a subpath of the other path), raise ValueError.

    with_name(self, name)
        Return a new path with the file name changed.

    with_suffix(self, suffix)
        Return a new path with the file suffix changed.  If the path
        has no suffix, add given suffix.  If the given suffix is an empty
        string, remove the suffix from the path.

    ----------------------------------------------------------------------
    Readonly properties inherited from pathlib.PurePath:

    anchor
        The concatenation of the drive and root, or ''.

    drive
        The drive prefix (letter or UNC path), if any.

    name
        The final path component, if any.

    parents
        A sequence of this path's logical parents.

    parts
        An object providing sequence-like access to the
        components in the filesystem path.

    root
        The root of the path, if any.

    stem
        The final path component, minus its last suffix.

    suffix
        The final component's last suffix, if any.

        This includes the leading period. For example: '.txt'

    suffixes
        A list of the final component's suffixes, if any.

        These include the leading periods. For example: ['.tar', '.gz']
