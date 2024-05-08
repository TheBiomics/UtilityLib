# FileUtility

## Compress/uncompress

```py
from UtilityLib import PM

PM.uncompress("/mnt/DataDrive/data/plots.tgz")
PM.uncompress("/mnt/DataDrive/data/plots.tgz", "/mnt/DataDrive/data")
PM.uncompress("/mnt/DataDrive/data/plots.zip")
PM.compress_dir("/mnt/DataDrive/data/plots", 'zip')
PM.tgz("/mnt/DataDrive/data/plots")
PM.zip("/mnt/DataDrive/data/plots")
```
