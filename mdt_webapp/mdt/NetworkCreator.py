import sys, pickle, os.path
import numpy as np
from time import time
from collections import Counter
from sklearn.neighbors import KDTree

from mdt_webapp.mdt.Emissions import build_vehicle_kdtree
from mdt_webapp.mdt.Network import Network, Segment, Node, generate_progress_bar

from mdt_project.settings import TXT_DIR, JSON_DIR, CSV_DIR, OBJ_DIR

class Creator:
    def __init__(self, osm_path='osm_network.p', tt_path='tt_network.p', mdt_path='mdt_network.p'):
        self.osm_file = OBJ_DIR+osm_path
        self.tt_file = OBJ_DIR+tt_path
        self.mdt_file = OBJ_DIR+mdt_path

    def create_networks(self, osm=None, tt=None, mdt=False, verbose=False):
        """
        Creates specified networks.
        :param osm:               array of query files to build network from (no extension)
        :param tt:                bool denoting whether to build TOMTOM network
        :param mdt:               bool denoting whether to build MDT network
        :param verbose:           print network creation progress
        :return bool, bool, bool: denotes which networks were created
        """
        creating_osm = False
        if osm != None:
            creating_osm = True
            networks = []

            if verbose: print("Building network from queries:\n   {0}".format(osm))

            # Queries are read from the osm array, and their resulting networks
            # are stored in the networks array.
            for i in range(len(osm)):
                filename = TXT_DIR+osm[i]+".txt"
                file = open(filename)

                query = file.read().replace("\n", " ").replace("  ", "")
                file.close()
                    
                start_time = time()
                if verbose: print("Building OSM network {0} of {1}:".format(i + 1, len(osm)))
                networks.append(Network(query=query, verbose=verbose))
                end_time = time()
                if verbose: print('\n   ... Built network in {0}s'.format(round(end_time-start_time, 2)))
                    
            # All networks in the networks array are then merged together.
            if len(networks) > 1:
                for i in range(len(networks[1:])):
                    networks[0].merge_with_network(networks[i+1])

            # The final OpenStreetMaps network is saved to an object file.
            pickle.dump( networks[0], open( self.osm_file, "wb" ) )
            if verbose: print('OSM network saved to: {0}'.format(self.osm_file))

        if tt != None:
            
            # Only one TOMTOM json file can be used to create a network.
            start_time = time()
            tt_network = Network(filename=JSON_DIR+tt, verbose=verbose)
            end_time = time()
            if verbose: print('\n   ... Built network in {0}s'.format(round(end_time-start_time, 2)))

            pickle.dump(tt_network, open( self.tt_file, "wb" ))
            if verbose: print('TOMTOM network saved to: {0}'.format(self.tt_file))

        if mdt:
            if os.path.isfile(self.osm_file) and os.path.isfile(self.tt_file):

                if verbose: print('Building MDT network:')
                osm_network = pickle.load( open( self.osm_file, "rb" ) )
                tt_network = pickle.load( open( self.tt_file, "rb" ) )

                # A KD tree is build for the UKDT count points and nodes in
                # the TOMTOM network.
                tt_keys, tt_kdt = tt_network.build_KDTree()
                vehicle_kdtree, vehicle_data = build_vehicle_kdtree(CSV_DIR+'count_points.csv')
                    
                osm_segments = osm_network.get_network_segments()
                tt_segments = tt_network.get_network_segments()

                count = 1
                no_segments = len(osm_segments)

                # All segments in the OSM network are iterated through.
                for key in osm_segments.keys():
                    if verbose: generate_progress_bar(count, no_segments, "{0} of {1} ({2}%)".format(count, no_segments, round(count*100/no_segments, 1)), prefix='   ... Merging segments: ')
                    segment = osm_segments[key]
                    coors = segment.get_coors()
                    street_name = segment.get_attributes()['streetName']

                    # An closest_segments array is initialised.
                    closest_segments = []
                    for coor in coors:

                        # For each coordinate in the OSM segment, the TOMTOM's KD tree is queried
                        # for the closest 3 nodes.
                        dist, ind = tt_kdt.query(np.array([[coor[0], coor[1]]]), k=3) 
                        for index in ind[0]:

                            # The segments attached to each of these 3 TOMTOM nodes are added to the
                            # closest_segments array.
                            attached = tt_network.get_network_nodes()[tt_keys[index]].get_attached()
                            closest_segments += attached

                    # All segments in the closest_segments array are ordered by how frequently they appear.
                    closest = max(set(closest_segments), key=closest_segments.count)
                    common_keys = list(dict.fromkeys([item for items, c in Counter(closest_segments).most_common() for item in [items] * c]))
                    best_fit_found = False

                    # These are then iterated through, starting with the most common.
                    for tt_key in common_keys:
                        try:
                            seg_attributes = tt_segments[tt_key].get_attributes()

                            # Segments are matched if they share the same street name and have non-zero flow data.
                            if not any(0 in sl for sl in seg_attributes['flowData']):
                                if seg_attributes['streetName'] == street_name:
                                    segment.set_attribute('flowData', tt_segments[tt_key].get_attributes()['flowData'])
                                    best_fit_found = True
                                    break
                        except KeyError:
                            continue

                    # If no match was found, the segment is given empty flow data.
                    if not best_fit_found: segment.set_attribute('flowData', tt_segments[common_keys[0]].get_attributes()['flowData'])

                    if sum(segment.get_flow_measures(3)) / len(segment.get_flow_measures(3)) != 0:

                        # The coordinates of the centre of each segment is found.
                        centre_index = float(len(coors))/2
                        if centre_index % 2 != 0:
                            centre = coors[int(centre_index - .5)]
                        else:
                            centre = coors[int(centre_index) - 1]

                        # The centre is used to query the UKDT count points data to get the
                        # vehicle proportions.
                        dist, ind = vehicle_kdtree.query(np.array([[centre[0], centre[1]]]), k=1)
                        vehicle_types_prop = vehicle_data[ind[0][0]]
                        segment.set_attribute('vehicleProps', vehicle_types_prop)
                    
                    # If there are no observed vehicles, the segment is given 0 values as their
                    # proportions.
                    else: segment.set_attribute('vehicleProps', [0, 0, 0, 0, 0])
                    count += 1
                
                # The final MDT network is then stored as an object file.
                if verbose: print('\n   ... Built network.')
                pickle.dump( osm_network, open( self.mdt_file, "wb" ) )
                if verbose: print('MDT network saved to: {0}'.format(self.mdt_file))

            else: print("Could not find '{0}' and/or '{1}'".format(self.osm_file, self.tt_file))

        return creating_osm, tt, mdt