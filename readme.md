# About UtilityLib2
* Provided ready to use functions to process, read, write, list files and directories and more...

# Examples

```python
# Append package path to PYTHONPATH or use sys.path.append method to append parent directory's path

from UtilityLib2 import EU
EU.filename("filepath/filename.ext1.ext2")

from UtilityLib2 import UtilityManager as UM
UM().filename("filepath/filename.ext1.ext2")

import UtilityLib2 as UL
UL.UM.filename("filepath/filename.ext1.ext2")
UL.UtilityManager().filename("filepath/filename.ext1.ext2")

```

## Quickly compress files to tar.gz (tgz) format and remove the directory
Later the files can be read directly from the tgz compressed file

```python
_eg_files = EU.search(f"{path_scrapped_queries}/eg-Downloads", "*.csv")
EU.add_tgz_files(f"{path_scrapped_queries}/eg-Downloads.tgz", _eg_files)
EU.delete_path(f"{path_scrapped_queries}/eg-Downloads")
```

# Version Updates

## 2.6
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
* Implemented ready to go import `from UtilityLib2 import EU`
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
