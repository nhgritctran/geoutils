import numpy as np
import pandas as pd
from tqdm import tqdm
from scipy import spatial

# show all columns in pandas
pd.set_option("display.max_columns", None)


class GeoImputation:

    def __init__(self):
        pass

    @staticmethod
    def closest_location(ref_coordinates, target_coordinate):
        """
        used to find the closest location to target_coordinate
        :param ref_coordinates: list of tuples of reference coordinates
        :param target_coordinate: tuple of a pair of coordinate
        :return: location, a tuple of the closest location
        """

        # create model with reference data
        model = spatial.KDTree(ref_coordinates)

        # find the closest location
        i = int(model.query(target_coordinate)[1])
        location = ref_coordinates[i]

        return location

    def impute_col(self, df, col2impute, keep_coordinate=False):
        """
        used to impute a column with missing data based on coordinates
        :param df: dataframe with "latitude", "longitude" & column to impute
        :param col2impute: column contain missing data, must have non-missing data
        :param keep_coordinate: keep or drop column coordinate, created for imputation
        :return: dataframe with imputed values
        """

        # reset index just in case
        df = df.reset_index(drop=True)

        # add coordinate column
        df["current_loc"] = list(zip(df["latitude"],
                                     df["longitude"]))
        df["coordinate"] = df["current_loc"].copy()

        # reference coordinates
        ref_df = df.loc[
            (df[col2impute] != "None") &
            (~df[col2impute].isna())
            ].reset_index()
        ref_coordinates = ref_df["coordinate"].to_list()

        # impute missing values
        ids = df.loc[
            (df[col2impute] == "None") |
            (df[col2impute].isna())
            ].index.tolist()

        print(f"Imputing {len(ids)} data points based on {len(ref_coordinates)} known data points.")
        for i in tqdm(ids):
            try:
                coordinate = df.iloc[i, df.columns.get_loc("coordinate")]
            except Exception as e:
                print(f"{type(e)}: {e}")
                print(i, len(df))
                return
            new_loc = self.closest_location(ref_coordinates, coordinate)
            new_val = ref_df.loc[
                (ref_df["coordinate"] == new_loc) &
                ((~ref_df[col2impute].isna()) &
                 (ref_df[col2impute] != "None")), col2impute
            ].unique()
            new_val = np.mean(new_val)  # this is to catch cases where 2 or more values returned
            df.iloc[i, df.columns.get_loc(col2impute)] = new_val
            df.iat[i, df.columns.get_loc("coordinate")] = new_loc

        if keep_coordinate:
            df.rename({"coordinate": "imputed_loc"}, axis=1, inplace=True)
        else:
            df.drop(["coordinate", "current_loc"], axis=1, inplace=True)

        # report
        total_count = len(ids)
        failed_count = len(df.loc[df[col2impute].isna()])
        print("##########")
        print()
        print("Total number of stations: ", total_count)
        print()
        print("Successfully mapped: ", total_count - failed_count)
        print()
        if total_count != 0:
            print("Success rate: ", (total_count - failed_count) / total_count * 100, "%")
            print()

        return df
