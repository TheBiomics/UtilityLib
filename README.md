# UtilityLib
UtilityLib is a Python package that provides a collection of ready-to-use functions for various file and directory operations, data processing tasks, and more.

# Installation

* You can install UtilityLib via pip or by copying the UtilityLib directory into your project.
* Using pip: `pip install UtilityLib`
* Using GitHub: `pip install git+https://github.com/yourusername/UtilityLib.git`

# Usage/Examples

Here are some examples demonstrating the usage of UtilityLib:

## Filename Extraction
```python

# Method 1
from UtilityLib import EU
EU.filename("filepath/filename.ext1.ext2")

# Method 2
from UtilityLib import UtilityManager as UM
UM().filename("filepath/filename.ext1.ext2")
```
## Project Configuration Management

```python
# Method 3
import UtilityLib as UL
UL.UM.filename("filepath/filename.ext1.ext2")
UL.UtilityManager().filename("filepath/filename.ext1.ext2")

# Method 4
from UtilityLib import ProjectManager
_pm = ProjectManager(
  path_bases=("/mnt/D/DataDrive", "D:/path-windows")
  version=2,
  subversion=202211
  )
_pm.config.new_key.deeper_new_key = "new_value"

# Update Old Config
_pm.update_config()

# Save as a new version but later change key
_pm.update_config(subversion=20221103)

```

## Compress Files to tar.gz Format

```python
_wos_files = EU.search(f"{path_scrapped_queries}/WOS-Downloads", "*.csv")
EU.add_tgz_files(f"{path_scrapped_queries}/WOS-Downloads.tgz", _wos_files)
EU.delete_path(f"{path_scrapped_queries}/WOS-Downloads")
```

# Updates/Revisions/Versions

## 2.10
* Added multi processing
* Method extension to add/update new method to the existing class object
* Method caching to speed up

## 2.9
## 2.8
* Method aliases
* Setup whl build system

## 2.6
### 20221103
* Added `ProjectManager`
  - Dot notion to access or deep nested objected
  - Can hold data by pickling and unpickling (Could there be any data loss due to protocol version change?)
  - class to keep track of configuration
  - persistent storage
  - Storage by pickling and unpickling

### 20221018
* Class `DataUtility` for quick processing of text, numbers or objects or frequently used libraries
* `require_form` method to include libraries from external folder

### 20220923
* Upgraded `FileSystemUtility.list_zipfile` to `FileSystemUtility.list_zip_files`

### 20220921
* Added cli argument parser
* ITERTOOLS product and combinations method

### 20220914
* Added single static `update_attributes` method and removed `__update_attr` method from individual class

## 2.5.20220908
* Implemented ready to go import `from UtilityLib import EU`
* Param changes in EU.combination method

## 2.5.20220905
* Added new methods
* Major changes (check commit)
  - Removed json parameter from FileSystemUtility.get_file
* Minor changes (check commit)

## 2.5.20220818
* Package reusability enhancement

## 2.4.20220129
* Initial version
