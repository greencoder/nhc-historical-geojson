import datetime
import json
import os
import sys

class Storm(object):

    def __init__(self, basin, number, year, name, num_entries):
        self.basin = basin
        self.number = number
        self.year = year
        self.name = name
        self.features = []
        self.expected_num_features = num_entries

    def to_manifest_dict(self):
        """ Returns the object as a dictionary used in the manifest file """
        return {
            'name': self.name,
            'year': self.year,
            'number': self.number,
        }

    @property
    def linestring_feature(self):
        """ Returns a linestring geojson feature of the storm path """
        coords = [(feat.longitude, feat.latitude) for feat in self.features]
        return {
            'type': 'Feature',
            'properties': {},
            'geometry': {
                'type': 'LineString',
                'coordinates': coords,
            }
        }

    @property
    def filename(self):
        """ Returns the name that can be used as a filename base """
        fn = '%s-%s-%s-%s' % (self.year, self.basin, self.number, self.name)
        return fn.lower()

class Entry(object):

    def __init__(self, datetime_utc, ident, status, lat, lng, wspeed, pressure):
        self.datetime_utc = datetime_utc
        self.identifier_code = ident
        self.system_status = status
        self.latitude = lat
        self.longitude = lng
        self.wind_speed = wspeed
        self.pressure_mb = pressure

    def to_feature_dict(self):
        """ Returns the entry as a geojson point feature """
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [
                    self.longitude,
                    self.latitude,
                ],
            },
            'properties': {
                'id-code': self.identifier_code,
                'status': self.system_status,
                'wind-speed': self.wind_speed,
                'datetime-utc': self.datetime_utc,
                'pressure-mb': self.pressure_mb,
            }
        }

if __name__ == '__main__':

    lines = {'atlantic': None, 'pacific': None}

    with open('atlantic.txt', 'r') as f:
        lines['atlantic'] = [line.strip() for line in f.readlines()]

    with open('pacific.txt', 'r') as f:
        lines['pacific'] = [line.strip() for line in f.readlines()]

    ATLANTIC_STORMS = []
    PACIFIC_STORMS = []
    
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))

    for basin_name in ('atlantic', 'pacific'):

        print 'Basin: %s' % basin_name

        storms = []
        current_storm = None

        for line in lines[basin_name]:

            # Split up the comma-delimited string
            parts = [p.strip() for p in line.split(',')]

            # See if it's a header line
            if line.startswith('AL') or line.startswith('EP') or line.startswith('CP'):

                # The first chunk contains positional data
                basin = parts[0][0:2]
                number = parts[0][2:4]
                year = parts[0][4:8]

                # The second piece is the storm name
                name = parts[1]

                # The third piece is the number of entries
                num_entries = int(parts[2])

                # Create a storm object
                storm = Storm(basin, number, year, name, num_entries)
                storms.append(storm)

                # Assign a state variable so we know where storm entries
                # should get assigned to
                current_storm = storm

            # If it's not a header line, then it must be a storm track entry
            else:

                # The first part contains positional data about the date
                year = parts[0][0:4]
                month = parts[0][4:6]
                day = parts[0][6:8]

                # The second part contains positional data about the time
                hour = parts[1][0:2]
                minute = parts[1][2:4]

                # Create a datetime object in ISO format
                datetime_utc = '%s-%s-%s %s:%s:00+00:00' % (year, month, day, hour, minute)

                # The third part contains an optional record identifier
                # See record_identifiers.txt for details. Note that
                # these are often blank
                identifier_code = parts[2]

                # The fourth part contains the status. See system_status.txt
                # for details.
                system_status = parts[3]

                # The fifth part contains the latitude with a 'N' or 'S'
                # in the last position. We need to change this to '-' if 'S'
                try:
                    latitude = float(parts[4][:-1])
                except IndexError:
                    print 'Index Error'
                    print parts
                    sys.exit()

                # If it's in the southern hemisphere, subtract it from zero
                # to make it a negative number
                if parts[4][-1] == 'S':
                    latitude = 0 - latitude

                # The sixth part contains the longitude with a 'E' or 'W'
                # in the last position
                longitude = float(parts[5][:-1])

                # If it's in the eastern hemisphere, subtrack it from zero
                # to make it a negative number
                if parts[5][-1] == 'W':
                    longitude = 0 - longitude

                # The seventh part is the maximum sustained wind speed
                wind_speed = float(parts[6])

                # The eigth part is the minimum pressure in millibars
                pressure_mb = float(parts[7])

                # Create an entry object
                entry = Entry(datetime_utc, identifier_code, system_status, latitude, longitude, \
                    wind_speed, pressure_mb)

                # Add this new entry to the current storm
                current_storm.features.append(entry)

        # Save the storms so we can write out the master list later
        if basin_name == 'atlantic':
            ATLANTIC_STORMS = storms
        else:
            PACIFIC_STORMS = storms

        # Output the storms as geojson files
        for storm in storms:

            if len(storm.features) != storm.expected_num_features:
                sys.exit('We have the wrong number of features for storm %s' % storm.filename)

            # Create a GeoJSON feature collection
            output = {
                'type': 'FeatureCollection',
                'features': [f.to_feature_dict() for f in storm.features],
                'properties': {
                    'name': storm.name,
                    'basin': storm.basin,
                    'year': storm.year,
                    'number': storm.number
                }
            }

            # Add the track line string feature to our features
            output['features'].append(storm.linestring_feature)

            # Create the path for the output
            directory_path = 'output/' + basin_name + '/' + storm.year + '/'
            directory_filepath = os.path.join(CUR_DIR, directory_path)
            
            # Make sure the directory exists
            if not os.path.exists(directory_filepath):
                os.makedirs(directory_filepath)

            # Skip the file if it's Central Pacific - the linestrings don't work
            if storm.filename.startswith('%s-cp-' % storm.year):
                continue

            # Write out the file
            filepath = os.path.join(directory_filepath, '%s.geojson' % storm.filename)
            with open(filepath, 'w') as f:
                f.write(json.dumps(output, indent=4))

    # Create a manifest file that lists all the available storms
    manifest = {
        'created-at': datetime.datetime.utcnow().isoformat(),
        'atlantic-storms': [s.to_manifest_dict() for s in ATLANTIC_STORMS],
        'pacific-storms': [s.to_manifest_dict() for s in PACIFIC_STORMS],
    }

    print 'Writing Manifest File.'
    with open('output/manifest.json', 'w') as f:
        f.write(json.dumps(manifest, indent=4))

