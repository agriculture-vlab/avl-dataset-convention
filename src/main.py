import pyproj

from dataset import from_crs84
from dataset import new_dataset

CRS_UTM_33N = pyproj.crs.CRS(32633)


def main():
    variables = [
        (
            'var_a',
            'float32',
            dict(
                long_name='Variable A',
                # standard_name='...',  # if exists
            )
        ),
        (
            'var_b',
            'uint16',
            dict(
                long_name='Variable B',
                # standard_name='...',  # if exists
                flag_meanings="quality_good sensor_nonfunctional outside_valid_range",
                flag_values="1, 2, 3"
            ),
        )
    ]

    dataset_global = new_dataset(width=3600,
                                 height=1800,
                                 x_res=3600 / 360,
                                 variables=variables)

    dataset_global \
        .chunk(dict(lon=360, lat=360, time='auto')) \
        .to_zarr('dataset_global.zarr')

    x_start, y_start = from_crs84((10, 52), CRS_UTM_33N)

    dataset_utm33n = new_dataset(width=1024,
                                 height=1024,
                                 x_start=x_start,
                                 y_start=y_start,
                                 x_name='x',
                                 y_name='y',
                                 x_units='meters',
                                 y_units='meters',
                                 crs=CRS_UTM_33N,
                                 variables=variables)

    dataset_utm33n \
        .chunk(dict(x=512, y=512, time='auto')) \
        .to_zarr('dataset_utm33n.zarr')


if __name__ == '__main__':
    main()
