## nucleiFetch
Quick and dirty tility that helps download nuclei templates from various sources in one place. Just run it with Python3 and that's pretty much it.

Creates directories:

|Directory|Description|
|---------|-----------|
|templates-latest |All tempaltes fetched during the last execution
|templates-previous |All templates fetched from the previous execution
|templates-onlynew |The difference between the two above
|tmp |Temporary directory used for cloning
