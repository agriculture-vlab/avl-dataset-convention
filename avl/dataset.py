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


from typing import Dict, Any, Tuple, List, Union

import numpy as np
import pandas as pd
import pyproj
import xarray as xr

CRS_CRS84 = pyproj.crs.CRS.from_string("CRS84")

DEFAULT_METADATA = dict(
    Conventions="CF-1.7",
    title='AVL test dataset',
    summary='This dataset is used to demonstrate the AVL'
            ' common dataset convention',
    keywords='ESA, AVL, Agriculture, EO'
)


def new_dataset(
        xy_size: Tuple[int, int] = (3600, 1800),
        xy_tile_size: Union[int, Tuple[int, int]] = None,
        xy_names: Tuple[str, str] = ('lon', 'lat'),
        xy_dtype: np.dtype = 'float64',
        xy_units: Union[str, Tuple[str, str]] = ('degrees_east',
                                                 'degrees_north'),
        xy_res: Union[float, Tuple[float, float]] = 360 / 3600,
        xy_start: Tuple[float, float] = (-180, -90),
        inverse_y: bool = False,
        time_name: str = 'time',
        time_dtype: np.dtype = 'datetime64[s]',
        time_units: str = 'seconds since 1970-01-01T00:00:00',
        time_calendar: str = 'proleptic_gregorian',
        time_periods: int = 5,
        time_res: str = "1D",
        time_start: str = '2010-01-01T00:00:00',
        use_cftime: bool = False,
        drop_bounds: bool = False,
        variables: List[Tuple[str, str, Dict[str, Any]]] = None,
        crs: Union[str, pyproj.CRS] = None,
        metadata: Dict[str, Any] = None
) -> xr.Dataset:
    """
    Create a new sample dataset. Useful for creating cubes templates with
    predefined coordinate variables and metadata.

    The 3-tuple items of the *variables* list are
        1. variable name
        2. numpy data type
        3. variable metadata

    :param xy_size: Number of spatial x,y grid cells.
        Defaults to (3600, 1800).
    :param xy_tile_size: Optional spatial tile size in grid cells.
        Defaults to None (= automatic chunking).
    :param xy_names: Names of the x,y coordinate variables.
        Defaults to ('lon', 'lat).
    :param xy_dtype: Data type of both x and y coordinate.
        Defaults to 'float64'.
    :param xy_units: Units of the x,y coordinates.
        Defaults to ('degrees_east', 'degrees_north').
    :param xy_start: Minimum x,y values.
        Defaults to (-180, -90).
    :param xy_res: Spatial resolution in x,y directions.
        Defaults to 1.0.
    :param inverse_y: Whether to create an inverse y axis. Defaults to False.
    :param time_name: Name of the time coordinate variable. Defaults to 'time'.
    :param time_periods: Number of time steps. Defaults to 5.
    :param time_res: Duration of each time step. Defaults to `1D'.
    :param time_start: First time value. Defaults to '2010-01-01T00:00:00'.
    :param time_dtype: Numpy data type for time coordinates.
        Defaults to 'datetime64[s]'.
        If used, parameter 'use_cftime' must be False.
    :param time_units: Units for time coordinates.
        Defaults to 'seconds since 1970-01-01T00:00:00'.
    :param time_calendar: Calender for time coordinates.
        Defaults to 'proleptic_gregorian'.
    :param use_cftime: If True, the time will be given as data types
        according to the 'cftime' package. If used, the time_calendar
        parameter must be also be given with an appropriate value
        such as 'gregorian' or 'julian'. If used, parameter 'time_dtype'
        must be None.
    :param drop_bounds: If True, coordinate bounds variables are not created.
        Defaults to False.
    :param variables: Dictionary of data variables to be added.
        None by default.
    :param crs: pyproj-compatible CRS string or instance
        of pyproj.CRS or None
    :param metadata: Metadata to be included in global attributes.
    :return: A dataset instance
    """
    if isinstance(xy_size, int):
        xy_size = xy_size, xy_size
    if isinstance(xy_tile_size, int):
        xy_tile_size = xy_tile_size, xy_tile_size
    if isinstance(xy_units, str):
        xy_units = xy_units, xy_units
    if isinstance(xy_res, (int, float)):
        xy_res = xy_res, xy_res
    if isinstance(crs, str):
        crs = pyproj.CRS.from_string(crs)
    if use_cftime and time_dtype is not None:
        raise ValueError('If "use_cftime" is True,'
                         ' "time_dtype" must not be set.')

    width, height = xy_size
    x_name, y_name = xy_names
    x_units, y_units = xy_units
    x_start, y_start = xy_start
    x_res, y_res = xy_res

    x_is_lon = x_name == 'lon' or x_units == 'degrees_east'
    y_is_lat = y_name == 'lat' or y_units == 'degrees_north'

    x_end = x_start + width * x_res
    y_end = y_start + height * y_res

    x_res_05 = 0.5 * x_res
    y_res_05 = 0.5 * y_res

    x_data = np.linspace(x_start + x_res_05, x_end - x_res_05,
                         width, dtype=xy_dtype)
    y_data = np.linspace(y_start + y_res_05, y_end - y_res_05,
                         height, dtype=xy_dtype)

    x_var = xr.DataArray(x_data, dims=x_name, attrs=dict(units=x_units))
    y_var = xr.DataArray(y_data, dims=y_name, attrs=dict(units=y_units))
    if inverse_y:
        y_var = y_var[::-1]

    if x_is_lon:
        x_var.attrs.update(long_name='longitude',
                           standard_name='longitude')
    else:
        x_var.attrs.update(long_name='x coordinate of projection',
                           standard_name='projection_x_coordinate')
    if y_is_lat:
        y_var.attrs.update(long_name='latitude',
                           standard_name='latitude')
    else:
        y_var.attrs.update(long_name='y coordinate of projection',
                           standard_name='projection_y_coordinate')

    if use_cftime:
        time_data_p1 = xr.cftime_range(start=time_start,
                                       periods=time_periods + 1,
                                       freq=time_res,
                                       calendar=time_calendar).values
    else:
        time_data_p1 = pd.date_range(start=time_start,
                                     periods=time_periods + 1,
                                     freq=time_res).values
        time_data_p1 = time_data_p1.astype(dtype=time_dtype)

    time_delta = time_data_p1[1] - time_data_p1[0]
    time_data = time_data_p1[0:-1] + time_delta // 2
    time_var = xr.DataArray(time_data, dims=time_name)
    time_var.encoding['units'] = time_units
    time_var.encoding['calendar'] = time_calendar

    coords = {x_name: x_var, y_name: y_var, time_name: time_var}
    if not drop_bounds:
        x_bnds_name = f'{x_name}_bnds'
        y_bnds_name = f'{y_name}_bnds'
        time_bnds_name = f'{time_name}_bnds'

        bnds_dim = 'bnds'

        x_bnds_data = np.zeros((width, 2), dtype=np.float64)
        x_bnds_data[:, 0] = np.linspace(x_start, x_end - x_res,
                                        width, dtype=xy_dtype)
        x_bnds_data[:, 1] = np.linspace(x_start + x_res, x_end,
                                        width, dtype=xy_dtype)
        y_bnds_data = np.zeros((height, 2), dtype=np.float64)
        y_bnds_data[:, 0] = np.linspace(y_start, y_end - x_res,
                                        height, dtype=xy_dtype)
        y_bnds_data[:, 1] = np.linspace(y_start + x_res, y_end,
                                        height, dtype=xy_dtype)
        if inverse_y:
            y_bnds_data = y_bnds_data[::-1, ::-1]

        x_bnds_var = xr.DataArray(x_bnds_data,
                                  dims=(x_name, bnds_dim),
                                  attrs=dict(units=x_units))
        y_bnds_var = xr.DataArray(y_bnds_data,
                                  dims=(y_name, bnds_dim),
                                  attrs=dict(units=y_units))

        x_var.attrs['bounds'] = x_bnds_name
        y_var.attrs['bounds'] = y_bnds_name

        time_bnds_data = np.zeros((time_periods, 2),
                                  dtype=time_data_p1.dtype)
        time_bnds_data[:, 0] = time_data_p1[:-1]
        time_bnds_data[:, 1] = time_data_p1[1:]
        time_bnds_var = xr.DataArray(time_bnds_data,
                                     dims=(time_name, bnds_dim))
        time_bnds_var.encoding['units'] = time_units
        time_bnds_var.encoding['calendar'] = time_calendar

        time_var.attrs['bounds'] = time_bnds_name

        coords.update({x_bnds_name: x_bnds_var,
                       y_bnds_name: y_bnds_var,
                       time_bnds_name: time_bnds_var})

    attrs = dict(DEFAULT_METADATA)
    if metadata:
        attrs.update(metadata)

    attrs.update(
        **get_geospatial_attrs(
            (x_start, y_start, x_end, y_end),
            (x_res, y_res),
            crs if crs is not None else CRS_CRS84
        )
    )
    attrs.update(
        **get_time_coverage_attrs(
            (time_data_p1[0], time_data_p1[-1]),
            time_res
        )
    )

    data_vars = {}
    if variables:
        dims = (time_name, y_name, x_name)
        shape = (time_periods, height, width)
        for var_name, dtype, attrs in variables:
            attrs = dict(attrs or {})
            if crs is not None:
                attrs['grid_mapping'] = 'crs'
            data_vars[var_name] = xr.DataArray(
                np.zeros(shape, dtype=dtype),
                dims=dims,
                attrs=attrs
            )

    if crs is not None:
        data_vars['crs'] = xr.DataArray(0, attrs=crs.to_cf())

    dataset = xr.Dataset(data_vars=data_vars,
                         coords=coords,
                         attrs=attrs)

    chunks = {
        x_name: 'auto',
        y_name: 'auto',
        'time': 'auto',
    }
    if xy_tile_size is not None:
        x_tile_size, y_tile_size = xy_tile_size
        chunks.update({
            x_name: x_tile_size,
            y_name: y_tile_size,
        })

    return dataset.chunk(chunks=chunks)


def get_geospatial_attrs(
        bbox: Tuple[float, float, float, float],
        res: Tuple[float, float],
        crs: pyproj.CRS
) -> Dict[str, Any]:
    if crs.is_geographic:
        lon_min, lat_min, lon_max, lat_max = bbox
        lon_res, lat_res = res
    else:
        x1, y1, x2, y2 = bbox
        x_res, y_res = res
        # center position
        xm1 = (x1 + x2) / 2
        ym1 = (y1 + y2) / 2
        # center position + delta
        xm2 = xm1 + x_res
        ym2 = ym1 + y_res
        transformer = pyproj.Transformer.from_crs(crs_from=crs,
                                                  crs_to=CRS_CRS84)
        xx, yy = transformer.transform((x1, x2, xm1, xm2),
                                       (y1, y2, ym1, ym2))
        lon_min, lon_max, lon_m1, lon_m2 = xx
        lat_min, lat_max, lat_m1, lat_m2 = yy
        # Estimate resolution (note, this may be VERY wrong)
        lon_res = abs(lon_m2 - lon_m1)
        lat_res = abs(lat_m2 - lat_m1)
    return dict(
        geospatial_lon_units='degrees_east',
        geospatial_lon_min=lon_min,
        geospatial_lon_max=lon_max,
        geospatial_lon_resolution=lon_res,
        geospatial_lat_units='degrees_north',
        geospatial_lat_min=lat_min,
        geospatial_lat_max=lat_max,
        geospatial_lat_resolution=lat_res,
        geospatial_bounds_crs='CRS84',
        geospatial_bounds=f'POLYGON(('
                          f'{lon_min} {lat_min}, '
                          f'{lon_min} {lat_max}, '
                          f'{lon_max} {lat_max}, '
                          f'{lon_max} {lat_min}, '
                          f'{lon_min} {lat_min}'
                          f'))',
    )


def get_time_coverage_attrs(
        time_range: Tuple[pd.Timestamp, pd.Timestamp],
        time_period: str,
) -> Dict[str, Any]:
    return dict(
        time_coverage_start=str(time_range[0]),
        time_coverage_end=str(time_range[1]),
        # TODO: Ensure ISO 8601:2004 duration format is used
        time_coverage_resolution=time_period,
        time_coverage_duration=f'{time_range[1] - time_range[0]}',
    )


def from_crs84(coord: Tuple[float, float], crs_to: pyproj.CRS):
    x, y = coord
    transformer = pyproj.Transformer.from_crs(crs_from=CRS_CRS84,
                                              crs_to=crs_to)
    return transformer.transform(x, y)
