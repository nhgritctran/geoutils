import time
import geopy
import requests
import numpy as np
import pandas as pd
from tqdm import tqdm

# show all columns in pandas
pd.set_option("display.max_columns", None)


class ReverseGeocoding:
    """
    This class contains methods for reverse geocoding
    """

    def __init__(self, api_key=""):

        # Google geocoding
        self.api_key = api_key
        self.ggeo_baseurl = "https://maps.googleapis.com/maps/api/geocode/json?latlng="
        self.gele_baseurl = "https://maps.googleapis.com/maps/api/elevation/json?locations="

        # USGS Elevation Point Query Service (EPQS)
        self.epqs_baseurl = "https://epqs.nationalmap.gov/v1/json?"

    def geo2zip(self, lat, lon, result_type="postal_code"):
        """
        Used for reverse geocoding with Google Geocoding API to get zip codes
        :param lat: latitude
        :param lon: longitude
        :param result_type: defaults to "postal_code"
        :return: 5 digit zop code
        """

        base_url = self.ggeo_baseurl
        url = f"{base_url}" + \
              f"{str(lat)},{str(lon)}" + \
              f"&result_type={result_type}" + \
              f"&key={self.api_key}"

        response = requests.get(url)
        result = response.json()["results"]

        if len(result) > 0:
            gzip = result[0]["address_components"][0]["long_name"]
        else:
            gzip = np.nan
        return gzip

    def epqs_elevation(self, lat, lon, units="Meters"):
        """
        Used for reverse geocoding with free EPQS API to get elevation
        :param lat: latitude
        :param lon: longitude
        :param units: accepts "Meters", "miles" or "km"
        :return: elevation
        """

        base_url = self.epqs_baseurl
        url = f"{base_url}" + \
              f"x={lon}&" + \
              f"y={lat}&" + \
              f"units={units}&" + \
              "wkid=4326&" + \
              "includeDate=False"

        # epqs always return status 200 but might not be able to return json
        # hence this try-except loop
        try:
            js = requests.get(url).json()
        except Exception as e:
            print(f"{type(e)}: {e}")
            try_count = 0
            js = {}
            # as API sometimes failed to parse json without clear reason
            # we will try to request 10 times before giving up
            while len(js) == 0 or not js:
                try:
                    js = requests.get(url).json()
                except Exception as e:
                    print(f"{type(e)}: {e}")
                    try_count += 1
                    js = {}
                    time.sleep(10)
                if try_count == 10:
                    break

        # check again in case all tries failed
        try:
            # check for real elevation values
            if (js["value"] > -450) and (js["value"] < 9000):
                elevation = js["value"]
            else:
                elevation = np.nan
        except Exception as e:
            print(f"{type(e)}: {e}")
            elevation = np.nan

        return elevation

    def google_elevation(self, df):
        """
        get elevation using Google API paid service
        :param df: input df with "latitude" and "longitude" columns
        :return: df with "elevation" column added
        """

        # check api key
        if self.api_key == "":
            print("A valid Google API key is required.")
            return df

        # google elevation api allows up to 512 locations per query
        # here  we divide lat, lon pairs into chunks of 500
        df["glocations"] = df["latitude"].astype(str) + "%2C" + df["longitude"].astype(str)
        locations = df["glocations"].tolist()
        n_chunks = len(locations) // 500 + 1
        chunks = []
        for i in range(n_chunks):
            chunks.append(locations[i * 500:(i + 1) * 500])

        # make api requests with chunks of location
        base_url = self.gele_baseurl
        outputs = []
        for chunk in tqdm(chunks):
            loc_string = "%7C".join(chunk)
            url = f"{base_url}" + \
                  f"{loc_string}" + \
                  f"&key={self.api_key}"
            response = requests.get(url)

            if response.status_code == 200:
                results = response.json()["results"]

                if len(results) > 0:
                    ele_list = [i["elevation"] for i in results]
                else:
                    ele_list = list(np.empty(len(results)).fill(np.nan))
                outputs = outputs + ele_list

            else:
                print(f"Failed attempt with status code {response.status_code}")
                print(f"Failed url: {url}")
                print()
                return

        df.loc[:, "gelevation"] = outputs

        return df

    def get_zip(self, df, zip_column=None, use_geopy=True):
        """
        Used to get zip code for a dataframe containing "latitude" and "longitude" columns
        :param df: dataframe containing "latitude" and "longitude" columns
        :param zip_column: name of existing zip code column, if any
        :param use_geopy: defaults to True - use GeoPy then Google API, else use only Google API
        :return: dataframe with columns "geopy_zip" (if use_geopy), "gzip" and "zip3"
        """

        total_count = len(df)

        if not zip_column:
            col_name = "zip"

        # GeoPy
        if use_geopy:
            print(f"Zip mapping {total_count} stations with GeoPy")
            geolocator = geopy.Nominatim(user_agent="1234")
            df["geopy_location"] = [geolocator.reverse((x, y)) for x, y in tqdm(zip(df["latitude"], df["longitude"]))]
            # data_processing
            zip_list = []
            for i in df["geopy_location"]:
                # print(i.raw["address"])
                try:
                    zip_list.append(i.raw["address"]["postcode"])
                except Exception as e:
                    print(f"{type(e)}: {e}")
                    zip_list.append(np.nan)
            df.loc[:, f"geopy_{col_name}"] = zip_list.copy()
            df.loc[:, "_zip"] = zip_list.copy()
        else:
            if not zip_column:
                df.loc[:, "_zip"] = np.nan
            else:
                df.loc[:, "_zip"] = df[zip_column].copy()
        zip_failed_count = len(df.loc[df["zip"].isna()])

        print("##########")
        print()

        # Google Geocoding
        print(f"Zip mapping {zip_failed_count} remaining stations with Google Geocoding")

        # data processing
        df.loc[:, "gzip"] = df["_zip"].copy()
        ids = df.index[df["gzip"].isna()].tolist()
        for i in tqdm(ids):
            lat = df.iloc[i, df.columns.get_loc("latitude")]
            lon = df.iloc[i, df.columns.get_loc("longitude")]
            df.iloc[i, df.columns.get_loc("gzip")] = self.geo2zip(lat, lon)
        df.loc[~df["gzip"].isna(), "zip3"] = df["gzip"].str[:3]
        df.loc[df["zip3"].isna(), "zip3"] = np.nan
        df.drop(columns="_zip", inplace=True)

        # report
        gzip_failed_count = len(df.loc[df["gzip"].isna()])
        print("##########")
        print()
        print("Total number of stations: ", total_count)
        print()
        print("Successfully mapped: ", total_count - gzip_failed_count)
        print()
        if total_count != 0:
            print("Success rate: ", (total_count - gzip_failed_count) / total_count * 100, "%")
            print()

        return df

    def get_elevation(self, df, methods="epqs"):
        """
        generate elevation from latitude and longitude data
        :param df: input dataframe, must have "latitude" and "longitude" columns
        :param methods: accepts "eqps" (free) or "google" (paid)
        :return: dataframe with column "elevation" added
        """

        if methods == "epqs":
            # missing values ids
            ids = df.index[
                (df["elevation"] == "None") |
                (df["elevation"].isna())
                ].tolist()
            total_count = len(ids)

            # mapping elevation
            print(f"Elevation mapping {total_count} locations.")
            for i in tqdm(ids):
                lat = df.iloc[i, df.columns.get_loc("latitude")]
                lon = df.iloc[i, df.columns.get_loc("longitude")]
                df.iloc[i, df.columns.get_loc("elevation")] = self.epqs_elevation(lat, lon)

            # report
            elevation_failed_count = len(df.loc[df["elevation"].isna()])
            print("##########")
            print()
            print("Total number of stations: ", total_count)
            print()
            print("Successfully mapped: ", total_count - elevation_failed_count)
            print()
            if total_count != 0:
                print("Success rate: ", (total_count - elevation_failed_count) / total_count * 100, "%")
                print()

            return df

        elif methods == "google":
            df = self.google_elevation(df)

            return df
