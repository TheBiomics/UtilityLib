# About UtilityLib
* Provided ready to use functions to process, read, write, list files and directories and more...

# Installation

* Install using source from github using python's pip module
* Copy the UtilityLib directory in the project
* `pip install UtilityLib` under any python envrironment

# Examples

```python
# Append package path to PYTHONPATH or use sys.path.append method to append parent directory's path

# 1
from UtilityLib import EU
EU.filename("filepath/filename.ext1.ext2")

# 2
from UtilityLib import UtilityManager as UM
UM().filename("filepath/filename.ext1.ext2")

# 3
import UtilityLib as UL
UL.UM.filename("filepath/filename.ext1.ext2")
UL.UtilityManager().filename("filepath/filename.ext1.ext2")

# 4
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

## Quickly compress files to tar.gz (tgz) format and remove the directory
Later the files can be read directly from the tgz compressed file

```python
_wos_files = EU.search(f"{path_scrapped_queries}/WOS-Downloads", "*.csv")
EU.add_tgz_files(f"{path_scrapped_queries}/WOS-Downloads.tgz", _wos_files)
EU.delete_path(f"{path_scrapped_queries}/WOS-Downloads")
```

# ToDo
- `require_from` GitHub
- Saving file hashes to check if file has changed ever since last accessed

# Requirements
* xmltodict
* sqlalchemy

# Version Updates

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

## 2.57.20220908
* Implemented ready to go import `from UtilityLib import EU`
* Param changes in EU.combination method

## 2.56.20220905
* Added new methods
* Major changes (check commit)
  - Removed json parameter from FileSystemUtility.get_file
* Minor changes (check commit)

## 2.5.20220818
* Package reusability enhancement

## 2.4.20220129
* Initial version
