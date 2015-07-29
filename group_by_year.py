import json
import os
import sys

CUR_DIR = os.path.dirname(os.path.realpath(__file__))

basins = ['atlantic', 'pacific']

for basin in basins:

    basin_dir = os.path.join(CUR_DIR, 'output/%s' % basin)
    years = [d for d in os.listdir(basin_dir)]

    for year in years:

        year_directory = os.path.join(basin_dir, year)

        # Make sure we're working with a directory
        if not os.path.isdir(year_directory):
            continue

        # Get all the files starting with the year string
        file_list = [f for f in os.listdir(year_directory)]

        # Aggregate all the features for this year
        features_for_year = []

        # Iterate over all the files and get out the polyline
        for filename in file_list:
            
            # Ignore any summary files
            if filename.endswith('_summary.geojson'):
                continue

            # Open the file and get the JSON data
            filepath = os.path.join(year_directory, filename)
            with open(filepath, 'r') as fh:
                json_contents = json.loads(fh.read())

            # Find the storm's properties
            try:
                storm_properties = json_contents['properties']
            except KeyError:
                print filepath
                print json_contents.keys()
                sys.exit()

            # Find the polyline
            features = json_contents['features']
            polyline_features = [f for f in features if f['geometry']['type'] == 'LineString']

            # Get the polyline (there will only be one)
            if len(polyline_features) != 1:
                sys.exit("Error: %s" % filename)
            else:
                polyline_feature = polyline_features[0]

            # Find the highest wind speed of any data point
            wind_speeds = []
            for feature in features:
                if feature['properties'].has_key('wind-speed'):
                    wind_speeds.append(feature['properties']['wind-speed'])

            # Figure out the storm classification
            sorted_wind_speeds = sorted(wind_speeds, reverse=True)
            max_speed_knots = sorted_wind_speeds[0]
            storm_properties['max-wind-speed-knots'] = max_speed_knots

            # Calcualte the classification on the Saffir-Simpson Scale
            if max_speed_knots <= 33:
                storm_properties['classification'] = 'TD'
            elif max_speed_knots <= 63:
                storm_properties['classification'] = 'TS'
            elif max_speed_knots <= 82:
                storm_properties['classification'] = 'HU1'
            elif max_speed_knots <= 95:
                storm_properties['classification'] = 'HU2'
            elif max_speed_knots <= 112:
                storm_properties['classification'] = 'HU3'
            elif max_speed_knots <= 136:
                storm_properties['classification'] = 'HU4'
            elif max_speed_knots >= 137:
                storm_properties['classification'] = 'HU5'
            else:
                storm_properties['classification'] = 'UNKNOWN'

            # Add this to the master list
            polyline_feature['properties'] = storm_properties
            features_for_year.append(polyline_feature)

        # Output the aggregated geojson
        filename = '%s_%s_summary.geojson' % (year, basin)
        output = {
            "type": "FeatureCollection",
            "features": features_for_year,
        }

        # Write the file
        filepath = os.path.join(year_directory, filename)
        with open(filepath, 'w') as f:
            f.write(json.dumps(output, indent=4))
