# The MIT License (MIT)
# Copyright (c) 2021 by the ESA AVL development team and contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import collections
from typing import Any, List, Union, Dict, Tuple, Callable

import numpy as np
import pyproj
import xarray as xr

_EXPECTED_GLOBAL_ATTRS = [
    'Conventions',
    'title',
    'summary',
    'sources',
    'history',
    'keywords',
    'id',
    'time_coverage_start',
    'time_coverage_end',
    'time_coverage_resolution',
    'geospatial_lon_min',
    'geospatial_lon_max',
    'geospatial_lon_resolution',
    'geospatial_lon_units',
    'geospatial_lat_min',
    'geospatial_lat_max',
    'geospatial_lat_resolution',
    'geospatial_lat_units',
]

_EXPECTED_VARIABLE_ATTRS = [
    ('long_name', None),
    ('standard_name', 'quantity'),
    ('units', 'quantity'),
]

WARNING = 'WARNING'
ERROR = 'ERROR'

Issue = Tuple[str, str]
Rule = Callable[[xr.Dataset], List[Issue]]


def verify_dataset(
        dataset: Union[str, collections.Mapping, xr.Dataset],
        level: str = 'ERROR',
        open_params: Dict[str, Any] = None
) -> List[Issue]:
    """
    Verifies that given *dataset* complies to the AVL dataset conventions.

    Args:
        dataset: The dataset. May be an `xarray.Dataset`, a path,
            or a Zarr store.
        level: Either "ERROR" (only errors)
            or "WARNING" (errors and warnings).
        open_params: Optional open parameters, ignored if *dataset*
            is an `xarray.Dataset`.
    Returns:
        A list of issues. Each issue is a 2-tuple comprising an issue
        severity level ("WARNING" or "ERROR") and the issue message.
        An empty list indicates a 100%-compliance.
    """
    if not isinstance(dataset, xr.Dataset):
        open_params = open_params or {}
        open_params.pop('decode_cf', None)
        dataset = xr.open_zarr(dataset,
                               decode_cf=False,
                               **(open_params or {}))
    all_issues = []
    for rule in get_rules():
        issues = rule(dataset)
        if issues:
            all_issues.extend(issues if level != ERROR
                              else [issue for issue in issues
                                    if issue[0] == ERROR])
    return all_issues


def get_rules() -> List[Rule]:
    return [
        check_global_attrs,
        check_time_coord,
        check_xy_coords,
    ]


def check_global_attrs(ds: xr.Dataset) -> List[Issue]:
    issues = []
    for attr_name in _EXPECTED_GLOBAL_ATTRS:
        issues += _check_global_attr(ds, attr_name)
    return issues


def check_time_coord(ds: xr.Dataset) -> List[Issue]:
    issues = []
    issues += _check_variable(ds, 'time')
    issues += _check_mono_inc(ds, 'time')

    time_dim = 'time'
    if 'time' in ds and ds.time.dims == (time_dim,):
        for var_name, var in ds.variables.items():
            if time_dim in var.dims and len(var.dims) > 1:
                if var.dims[0] != time_dim:
                    issues += _severe(f"first dimension of"
                                      f" variable {var_name!r}"
                                      f" must be {time_dim!r},"
                                      f" but dimensions are {var.dims!r}")

    return issues


def check_xy_coords(ds: xr.Dataset) -> List[Issue]:
    issues = []

    yx_dims = None

    x = ds.get('x')
    y = ds.get('y')
    if x is not None and y is not None:
        issues += _check_variable(ds, 'x')
        issues += _check_variable(ds, 'y')
        if x.ndim == 1 and y.ndim == 1:
            yx_dims = 'y', 'x'
            issues += _check_mono_inc(ds, 'x')
            issues += _check_mono_inc_or_dec(ds, 'y')
            issues += _check_crs(ds, 'crs')
        else:
            issues += _severe("coordinate variables 'x' and 'y' "
                              "must both be 1-D")

    lon = ds.get('lon')
    lat = ds.get('lat')
    if lon is not None and lat is not None:
        issues += _check_variable(ds, 'lon')
        issues += _check_variable(ds, 'lat')
        if lon.ndim == 1 and lat.ndim == 1:
            yx_dims = 'lat', 'lon'
            issues += _check_mono_inc(ds, 'lon')
            issues += _check_mono_inc_or_dec(ds, 'lat')
        elif lon.ndim == 2 and lat.ndim == 2:
            if lon.dims != ('y', 'x'):
                issues += _severe("dimensions of 'lat' must be ('y', 'x')")
            if lat.dims == ('y', 'x'):
                issues += _severe("dimensions of 'lat' must be ('y', 'x')")
            yx_dims = 'y', 'x'
        else:
            issues += _severe("coordinate variables 'lon' and 'lat' "
                              "must both be either 1-D or 2-D")

    if yx_dims is None:
        issues += _severe('no valid spatial coordinates found')
    else:
        y_dim, x_dim = yx_dims
        for var_name, var in ds.variables.items():
            if y_dim in var.dims and x_dim in var.dims:
                if var.dims[-2:] != yx_dims:
                    issues += _severe(f"last two dimensions of"
                                      f" variable {var_name!r}"
                                      f" must be {yx_dims!r},"
                                      f" but dimensions are {var.dims!r}")

    return issues


def _check_crs(ds, var_name):
    issues = _check_variable(ds, var_name)
    if var_name in ds:
        try:
            pyproj.CRS.from_cf(ds[var_name].attrs)
        except pyproj.exceptions.ProjError as e:
            issues += _severe(f"invalid {var_name!r} variable: {e}")
    return issues


def _check_1d_coord(ds, var_name):
    var = ds[var_name]
    issues = []
    if var.dims != (var_name,):
        issues += _severe(f"variable {var_name!r} must"
                          f" have a single dimension {var_name!r}")
    return issues


def _check_mono_inc(ds, var_name):
    issues = _check_1d_coord(ds, var_name)
    var = ds[var_name]
    var_diff = var.diff(dim=var_name)
    if np.issubdtype(var_diff.dtype, np.timedelta64):
        var_diff = var_diff.astype(np.float64)
    if not np.all(var_diff > 0):
        issues += _severe(f"values of variable {var_name!r} must be"
                          " strictly monotonically increasing")
    return issues


def _check_mono_inc_or_dec(ds, var_name):
    issues = _check_1d_coord(ds, var_name)
    var = ds[var_name]
    var_diff = var.diff(dim=var_name)
    if not (np.all(var_diff > 0) or np.all(var_diff < 0)):
        issues += _severe(f"values of variable {var_name!r} must be"
                          " strictly monotonically increasing or decreasing")
    return issues


def _check_variable(ds: xr.Dataset, var_name: str) -> List[Issue]:
    if var_name not in ds:
        return _severe(f'missing variable {var_name!r}')
    issues = []
    for attr_name, var_type in _EXPECTED_VARIABLE_ATTRS:
        if var_type == 'quantity' and _is_quantity_var(ds, var_name):
            issues += _check_variable_attr(ds, var_name, attr_name)
    return issues


def _check_variable_attr(ds: xr.Dataset,
                         var_name: str,
                         attr_name: str) -> List[Issue]:
    if attr_name not in ds[var_name].attrs:
        return _warning(f'missing attribute {attr_name!r}'
                        f' in variable {var_name!r}')
    return []


def _check_global_attr(ds: xr.Dataset,
                       attr_name: str) -> List[Issue]:
    if attr_name not in ds.attrs:
        return _warning(f'missing global attribute {attr_name!r}')
    return []


def _is_quantity_var(ds: xr.Dataset, var_name: str) -> bool:
    if var_name == 'crs':
        return False
    var = ds[var_name]
    return var.ndim > 0 and 'flag_names' not in var.attrs


def _warning(msg: str) -> List[Issue]:
    return [(WARNING, msg)]


def _severe(msg: str) -> List[Issue]:
    return [(ERROR, msg)]
