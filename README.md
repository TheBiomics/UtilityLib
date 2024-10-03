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
