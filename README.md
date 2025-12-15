[![PyPI Downloads](https://static.pepy.tech/personalized-badge/utilitylib?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLUE&right_color=BLACK&left_text=All)](https://pepy.tech/projects/utilitylib) [![PyPI Downloads](https://static.pepy.tech/personalized-badge/utilitylib?period=monthly&units=INTERNATIONAL_SYSTEM&left_color=BLUE&right_color=BLACK&left_text=This+Month)](https://pepy.tech/projects/utilitylib)

# UtilityLib
UtilityLib is a unified library of basic modules that provides a collection of ready-to-use functions for various file system oprerations and data processing.

# Installation

* You can install UtilityLib via pip or by copying the UtilityLib directory into your project.
* Using pip: `pip install UtilityLib`
* Using pip+GitHub: `pip install git+https://github.com/yourusername/UtilityLib.git`

# Usage/Examples

Here are some examples demonstrating how to use UtilityLib's key features:

## Initialize UtilityLib's ProjectManager or any other class in the chain

UtilityLib provides flexible import options for different use cases:

```python
# Initialize it with setting current working directory as base_path provided
from UtilityLib import ProjectManager
MyProj = ProjectManager(path_base="path/to/your/project/dir")

# Or change directory in runtime

MyProj.path_base = 'path/to/some-other/directory'

print(MyProj.config_version, MyProj.config_subversion, MyProj.path_base)

```

## File Path Operations

* Refer [UtilityLib.lib.path.EntityPath](./UtilityLib/lib/path.py)

```python
# Change current working directory

# List all files (Refer UtilityLib.lib.path.EntityPath for more options )

_proj_path = MyProj.path_base

# Walk Files and Dirs using iterator (memory efficient) or list them all
_walk_dirs  = _proj_path.walk_dirs
_walk_files = _proj_path.walk_filess

# List direct files and directories/folders in project
_all_files = _proj_path.files
_all_dirs  = _proj_path.dirs

# Get tree of the directory (Linux's tree equivalent)
print(_proj_path.tree) # use _proj_path.tree_gen (generator method) if you think there are too many files

# Pick matching file or search multiple files
_my_single_excel_file = _proj_path.get_match('*Excel-2025*.xlsx')
_my_jpg_files = _proj_path.search("*2025*.jpg")

# Tip: rename, move, or copy using (refer )

# Create new path on go, it returns UtilityLib.lib.path.EntityPath object
_my_new_sub_path: EntityPath = (MyProj.path_base / 'New-Dir' / 'Sub-Dir').validate()

# Use EntityPath delete method to delete files or folders. You need to turn off is_protected to delete else it raises warning
_my_new_sub_path.delete(is_protected=False)

```

### Some quick file operations

```python
_mfpo = _my_file_path_obj = (MyProj.path_base / 'My-Excel-File.xlsx')

print(_mfpo.stem, _mfpo.name, _mfpo.suffix) # Prints file names and extension

print(_mfpo.with_suffix('.2025-05-2022.xlsx')) # Changes file extension

print(_mfpo.created) # Prints date of the file creation
print(_mfpo.updated) #
print(_mfpo.exists()) # Does file exists?

print(_mfpo.copy('/New/Location/Copy-dir/'))
print(_mfpo.copy('/New/Location/Copy-dir/with-new-name.xlsx'))
print(_mfpo.move('/New/Location/Move-dir/with-new-name.xlsx'))

```

## Project Configuration Management

```python
from UtilityLib import ProjectManager

# Initialize project manager with cross-platform paths
MyProj = ProjectManager(
  path_bases=("/mnt/D/DataDrive", "D:/path-windows"),
  version=2,
  subversion=202211 # To load specific sub config
)

# Add new configuration values
MyProj.config.database.connection_string = "sqlite:///data.db"
MyProj.config.processing.batch_size = 1000

# Update existing configuration
MyProj.update_config()

# Save configuration with new subversion
MyProj.update_config(subversion=20221103)
```

## File Compression and Cleanup

```python
# Create compressed archive
MyProj.add_tgz_files("/data/WOS-Downloads.tgz", csv_files)

# Clean up original directory
MyProj.delete_path("/data/WOS-Downloads")

```

# Classes and Modules

* [UtilityLib](./UtilityLib/docs/UtilityLib.md)

* [EntityPath](./UtilityLib/docs/entity.md)
* [FileSystemUtility](./UtilityLib/docs/file.md)
* [CommandUtility](./UtilityLib/docs/cmd.md)
