# UtilityLib

# Updates/Revisions/Versions

## 2.16

## 2.12

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
