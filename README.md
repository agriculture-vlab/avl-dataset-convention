# Agriculture Virtual Lab (AVL)

This repository provides the documentation and a dedicated Python API for the 
ESA project _Agriculture Virtual Lab (AVL)_.

## Install AVL Python package

### From distribution

AVL has no distribution yet.

### From sources

The AVL Python package requires a conda Python environment:

```bash
$ conda install -c conda-forge pyproj s3fs xarray zarr
```

Or just `xcube`, which comes with all required packages 

```bash
$ conda install -c conda-forge xcube
```

Then, in the AVL project directory

```bash
$ python setup.py develop
```

Or with pip (so you can uninstall)

```bash
$ pip install --no-deps --editable .
```

## Build AVL documentation

The AVL documentation is generated using [MkDocs](https://www.mkdocs.org/) 
and plugin [MkApi](https://mkapi.daizutabi.net/). (Other `MkDocs` plugins 
can be found [here](https://github.com/mkdocs/mkdocs/wiki/MkDocs-Plugins).)

We require

```bash
$ pip install mkdocs
$ pip install mkapi
```

Then

```bash
$ mkdocs serve
```
or
```bash
$ mkdocs build
```

