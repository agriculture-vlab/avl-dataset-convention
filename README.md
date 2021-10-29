# avl-dataset-convention

Provides a dataset convention and example datasets for the AVL project.


## Install (from source)

Requires a conda Python environment with latest versions of 
* `pyproj`
* `s3fs` (optional)
* `xarray`
* `zarr`

```bash
$ python setup.py develop
```

## Functions

### Dataset compliance

Verify a dataset is compliant to AVL convention.

CLI:
```bash
$ avl verify <path or url> 
```

Python API:
```python
import s3fs
from avl.verify import verify_dataset

s3 = s3fs.S3FileSystem(anon=True)
store = s3fs.S3Map('agriculture-vlab-data-staging/avl/l3b/2020/bel/S2_L3B_LAI_31UFS.zarr', s3=s3)
dataset = xr.open_zarr(store) 
issues = verify_dataset(dataset)
```

### Example datasets

Generate a set of AVL sample datasets:

CLI:
```bash
$ avl new
```
