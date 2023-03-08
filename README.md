# geoutils - Tools developed to work with geospatial data.

# Description
Collection of tools developed for geocoding related tasks such as mapping zip code, elevation, e.g. It is expected that this repository would keep growing as more tools added for different types of geospatial data.

# Setup
Clone github repo:
```angular2html
!git clone https://github.com/nhgritctran/geoutils
```
Import tools of interests
````angular2html
from geoutils.geocoding import ReverseGeocoding
from geoutils.geoviz import Choropleth
from geoutils.imputation import GeoImputation
````

# Usage
## geocoding
Tools for mapping zip codes and elevation. In general, these tools include options for both free and paid services. The expectation is free service is not as comprehensive and paid service. Therefore, it is recommended to use paid service for work requires high data quality.

## geoviz
Tools for visualizing geospatial data. Currently supports US map at coordinate, county and state levels.

## imputation
It is common that there could be missing data in geospatial data. Geocoding services also do not guarantee to work all the time. This library uses data from the nearest known location for imputation. For that reason, it works best when missing data proportion is small (~20% or less) and it also depends on the coverage of known data.

# Dependencies
## geocoding
```angular2html
geopy
numpy
pandas
requests
time
tqdm
```

## geoviz
```angular2html
pandas
plotly
requests
```

## imputation
```angular2html
numpy
pandas
scipy
tqdm
```