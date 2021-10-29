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
@click.option('--output', '-o', 'output_dir_path',
              metavar="OUTPUT_DIR",
              default=".",
              help="Output directory. Defaults to current working directory.")
@click.option('--file', '-f', 'cache_file_path',
              metavar="CACHE_FILE",
              default=None,
              help="File that holds cached datasets' metadata (JSON format).")
@click.option('--cache', 'write_cache_only',
              is_flag=True,
              help="Write the CACHE_FILE only and exit."
                   " Ignored if JSON_FILE is not given.")
def cat(output_dir_path='.',
        cache_file_path=None,
        write_cache_only=False):
    """
    Generate the markdown catalogue of all available AVL datasets
    in the AWS S3 buckets.
    Output will be generated into directory ${OUTPUT_DIR}/catalogue.

    \b
    Examples
    --------

    Generate markdown catalogue of all datasets (reads from S3):

        $ avl cat

    Just fetch datasets' metadata from S3 and write to datasets.json,
    then exit:

        $ avl cat -f datasets.json --json

    Read datasets.json, then generate markdown catalogue:

        $ avl cat -f datasets.json

    """

    import json
    import os

    output_dir_path = output_dir_path or '.'

    def load_descriptors_from_store():
        from xcube.core.store import new_data_store
        import traceback

        store = new_data_store("s3",
                               root='agriculture-vlab-data-staging',
                               max_depth=5,
                               storage_options=dict(anon=True))
        descriptors = []
        for data_id in store.get_data_ids():
            click.echo(f"Fetching descriptor for {data_id!r}...")
            try:
                descriptor = store.describe_data(data_id)
                descriptors.append(descriptor.to_dict())
            except Exception as e:
                click.echo(f"Error: {e}")
                traceback_lines = list(traceback.format_tb(e.__traceback__))
                descriptors.append(
                    dict(data_id=data_id,
                         error=dict(message=f'{e}',
                                    traceback=traceback_lines))
                )
        return descriptors

    def load_descriptors_from_file(path):
        with open(path) as stream:
            return json.load(stream)

    def write_descriptors_to_file(path, descriptors):
        with open(path, 'w') as stream:
            json.dump(descriptors, stream, indent=2)

    def write_catalogue(descriptors):
        catalogue_dir = f'{output_dir_path}/catalogue'
        datasets_dir_name = 'datasets'
        datasets_dir = f'{catalogue_dir}/{datasets_dir_name}'
        os.makedirs(datasets_dir, exist_ok=True)
        with open(f'{catalogue_dir}/index.md', 'w') as fp_catalogue:
            fp_catalogue.write("# AVL Dataset Catalogue\n\n")
            for descriptor in descriptors:
                data_id = descriptor.get('data_id', '?')
                encoded_data_id = data_id.replace('/', '_')
                rel_data_id_path = f'{datasets_dir_name}/{encoded_data_id}.json'
                abs_data_id_path = f'{catalogue_dir}/{rel_data_id_path}'
                has_error = 'error' in descriptor
                fp_catalogue.write(
                    f"* [{data_id}]({rel_data_id_path})"
                    f"{' Error!' if has_error else ''}\n"
                )
                with open(abs_data_id_path, 'w') as fp_data_id:
                    json.dump(descriptor, fp_data_id, indent=2)

    def get_descriptors():
        if cache_file_path:
            if write_cache_only:
                descriptors = load_descriptors_from_store()
                write_descriptors_to_file(cache_file_path, descriptors)
                return None
            return load_descriptors_from_file(cache_file_path)
        else:
            return load_descriptors_from_store()

    def run():
        click.echo(f"Fetching descriptors...")
        descriptors = get_descriptors()
        if not descriptors:
            return

        click.echo(f"Converting {len(descriptors)} descriptors...")
        write_catalogue(descriptors)

    run()


@main.command()
@click.argument('dataset_path',
                metavar='DATASET')
@click.option('--level', '-l',
              type=click.types.Choice(["ERROR", "WARNING"]),
              default="WARNING",
              help="Level of messages to include.")
def ver(dataset_path: str, level: str):
    """
    Verify given dataset conforms to the AVL dataset convention.
    """
    from .verify import verify_dataset
    from .verify import WARNING
    from .verify import ERROR

    issues = verify_dataset(dataset_path, level=level)
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
