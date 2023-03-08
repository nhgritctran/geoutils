import pandas as pd
import plotly
import plotly.express as px
import requests


class Choropleth:

    def __init__(self):
        self.county_fips_url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

    def county_choropleth(self,
                          df,
                          color_by=None,
                          color_unit="",
                          color_max=None,
                          color_scale="Turbo",
                          title="",
                          slider_col=None):
        """
        used to generate us county choropleth map
        :param df: input df, must have "county" column
        :param color_by: name of columns containing values for coloring
        :param color_unit: name of unit of colored values, for use in legend
        :param color_max: max value for coloring
        :param color_scale: defaults to "Turbo", lookup plotly color_scale for more info
        :param title: plot title
        :param slider_col: column contain data for interactive slider
        :return: US choropleth map of county data
        """

        # get plotly county info
        response = requests.get(self.county_fips_url)
        counties = response.json()

        # assign value for animation_frame if any
        if slider_col:
            animation_frame = list(df[slider_col])
        else:
            animation_frame = None

        # assign max value for color scale
        if color_max:
            color_max = color_max
        else:
            color_max = df[color_by].max()

        # plot us county choropleth
        fig = px.choropleth(df,
                            geojson=counties,
                            locations=list(df["county"]),
                            color=list(df[color_by]),
                            color_continuous_scale=color_scale,
                            range_color=(0, color_max),
                            scope="usa",
                            labels={color_by: color_by},
                            animation_frame=animation_frame)
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig.show()

    def us_choropleth(self,
                      df,
                      locationmode=None,
                      color_by=None,
                      color_unit="",
                      color_max=None,
                      color_scale="Turbo",
                      title="",
                      dot_size=2,
                      slider_col=None):
        """
        used to generate US choropleth map
        :param df: dataframe with
                   "latitude" & "longitude" for locationmode=None;
                   "state" (state abbreviation) for locationmode="state";
                   "county" (county FIPS) for locationmode="county"
        :param locationmode: plotly location mode, defaults to None and use coordinates; accepts "state"
        :param color_by: name of columns containing values for coloring
        :param color_unit: name of unit of colored values, for use in legend
        :param color_max: max value for coloring
        :param color_scale: defaults to "Turbo", lookup plotly color_scale for more info
        :param title: plot title
        :param dot_size: size of plotted dots
        :param slider_col: column contain data for interactive slider
        :return: US choropleth map of data of interest
        """

        plotly.offline.init_notebook_mode()

        # setup markers
        if color_by:
            if color_unit:
                color_unit = f"({color_unit})"
            marker_dict = {"size": dot_size,
                           "autocolorscale": False,
                           "colorscale": color_scale,
                           "color": df[color_by],
                           "colorbar": {"title": f"{color_by} {color_unit}"}}
        else:
            marker_dict = {"size": dot_size}

        # main plot data
        if locationmode == "state":
            data = [{"type": "scattergeo",
                     "locations": df["state"],
                     "locationmode": "USA-states",
                     "marker": marker_dict}]

        elif locationmode == "county":
            self.county_choropleth(df=df,
                                   color_by=color_by,
                                   color_unit=color_unit,
                                   color_scale=color_scale,
                                   color_max=color_max,
                                   title=title,
                                   slider_col=slider_col)
            return

        elif not locationmode:
            data = [{"type": "scattergeo",
                     "lat": df["latitude"],
                     "lon": df["longitude"],
                     "marker": marker_dict}]

        # plot layout
        layout = {"title": title,
                  "geo": {"scope": "usa",
                          "projection": {"type": "albers usa"},
                          "showland": True,
                          "landcolor": "rgb(250,250,250)",
                          "subunitcolor": "rgb(217,217,217)",
                          "countrycolor": "rgb(217,217,217)",
                          "countrywidth": 0.5,
                          "subunitwidth": 0.5}}

        # plot
        plotly.offline.iplot({"data": data, "layout": layout})
