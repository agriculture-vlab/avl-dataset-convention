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

import click


@click.group()
def main():
    """Command-line tool for the ESA AVL project."""
    pass


@main.command()
@click.argument('dataset_path', metavar='DATASET')
def verify(dataset_path: str):
    """
    Verify given dataset conforms to the AVL convention.
    """
    from .verify import verify_dataset
    from .verify import WARNING
    from .verify import ERROR

    issues = verify_dataset(dataset_path)
    if not issues:
        click.echo('Ok, no issues found.')
    else:
        num_warnings = len([1 for level, _ in issues if level == WARNING])
        num_errors = len([1 for level, _ in issues if level == ERROR])
        click.echo(f'{num_errors} error(s)'
                   f' and {num_warnings} warnings(s) found:')
        for level, message in issues:
            click.echo(f'{level}: {message}')
        if num_errors > 0:
            raise click.ClickException('Dataset is not compliant')


@main.command()
def new():
    """
    Generate AVL sample dataset into current working directory.
    """
    from .dataset import from_crs84
    from .dataset import new_dataset
    from zarr.storage import ZipStore
    import pyproj

    def write_zarr(file_path: str, **dataset_kwargs):
        print(f'Writing {file_path}...')
        dataset = new_dataset(**dataset_kwargs)
        store = ZipStore(file_path + '.zip')
        dataset.to_zarr(store)

    # Note, we take values for color_bar_name from
    # https://matplotlib.org/stable/tutorials/colors/colormaps.html
    # TODO (forman): use Sentinel-2 band names and flags here which better
    #   represent the required examples.
    variables = [
        # A geo-physical variable
        (
            'var_a',
            'float32',
            dict(
                long_name='Variable A',
                # standard_name='...',  # if exists,
                units='mg/kg',
                color_bar_name='bone',
                color_value_min=0.0,
                color_value_max=0.75
            )
        ),
        # A quality flags variable
        (
            'var_b',
            'uint16',
            dict(
                long_name='Variable B',
                # standard_name='...',  # if exists
                flag_meanings="quality_good"
                              " sensor_nonfunctional"
                              " outside_valid_range",
                flag_values="1, 2, 3",
                color_bar_name='tab10',
                color_value_min=0,
                color_value_max=10
            )
        )
    ]

    write_zarr('dataset_global.zarr',
               xy_size=(7200, 3600),
               xy_tile_size=720,
               xy_res=360 / 7200,
               variables=variables)

    crs_utm_33n = pyproj.crs.CRS(32633)
    xy_start = from_crs84((10., 52.), crs_utm_33n)

    write_zarr('dataset_utm33n.zarr',
               xy_size=(2048, 2048),
               xy_tile_size=512,
               xy_start=xy_start,
               xy_names=('x', 'y'),
               xy_units='meters',
               crs=crs_utm_33n,
               variables=variables)


if __name__ == '__main__':
    main()
