# nch-historical-geojson

Turn the National Hurricane Center archives into individual GeoJSON files.

# Setup

First, grab the historical data archives from the [NHC data website](http://www.nhc.noaa.gov/data/) and save them locally. Scroll down to the 'Best Track Data (HURDAT2)' section and find the two database files.

*Note: The filenames below are the current ones as of this date (6/22/15), check the link above for updated versions each season.*

```
$ wget -O atlantic.txt http://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2014-060415.txt
$ wget -O pacific.txt http://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2014-060415.txt
```

Create an `output` directory, then create `atlantic` and `pacific` subdirectories in it:
```
$ mkdir -p output/atlantic
$ mkdir -p output/pacific
```

# Processing

With the [atlantic.txt](atlantic.txt) and [pacific.txt](pacific.txt) files in your current directory, run the `process.py` command:
```
$ python process.py
```

The script will run and put the resulting GeoJSON files in the [output/atlantic](output/atlantic) and [output/pacific][output/pacific] directories. It will also create a [manifest file][output/manifest.json] that lists all the storms in both basins.

