# Tools

## Dataset compliance

Verify given dataset conforms to the AVL dataset convention.

CLI:
```bash
$ avl ver --help
Usage: avl ver [OPTIONS] DATASET

  Verify given dataset conforms to the AVL dataset convention.

Options:
  -l, --level [ERROR|WARNING]  Level of messages to include.
  --help                       Show this message and exit. 
```

Python API:
```python
import xarray as xr
import s3fs
from avl.verify import verify_dataset

s3 = s3fs.S3FileSystem(anon=True)
store = s3fs.S3Map('agriculture-vlab-data-staging/avl/l3b/2020/bel/S2_L3B_LAI_31UFS.zarr', s3=s3)
dataset = xr.open_zarr(store) 
issues = verify_dataset(dataset)
```

## Synthetic example datasets

Generate AVL sample dataset into current working directory.

CLI:
```bash
$ avl new --help
Usage: avl new [OPTIONS]

  Generate AVL sample dataset into current working directory.

Options:
  --help  Show this message and exit.
```

## Generate simple catalogue

Generate the markdown page of all available AVL datasets in the AWS S3
buckets.

CLI:
```bash
$ avl cat --help
Usage: avl cat [OPTIONS]

  Generate the markdown page of all available AVL datasets in the AWS S3
  buckets.

Options:
  -f, --file JSON_FILE  JSON file path
  --json                Write the JSON_FILE and exit. Ignored if JSON_FILE is
                        not given.
  --help                Show this message and exit.
```
