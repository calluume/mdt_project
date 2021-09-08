import os, sys, json, math, random, overpy
import numpy as np
from time import sleep
from sklearn.neighbors import KDTree
from geopy.distance import distance
from os.path import basename
from zipfile import ZipFile

from mdt_project.settings import CSV_DIR,ZIP_DIR

class Network:
    def __init__(self, filename=None, query=None, verbose=False):
        """
        Create network from either JSON file or OSM query.
        :param filename: TOMTOM data file_path
        :param query:    Single OSM query
        :param verbose:  Print network creation progress
        """

        self.nodes = {}
        self.segments = {}
        
        # Networks are either created exclusively from
        # an OSM query or TOMTOM json file.
        if filename != None and query == None:
            print("Building from '{0}':".format(filename))
            self.build_from_file(filename, verbose)

        elif query != None and filename == None:
            self.build_from_query(query, verbose)

    def build_from_file(self, filename, verbose):
        """
        Builds network with TOMTOM data, downloaded in JSON format.
        :param filename: JSON file path
        :param verbose:  Print network creation progress
        """
        with open(filename) as json_file:
            data = json.load(json_file)

        if verbose: print('JSON File successfully loaded.')

        count = 1

        for segment in data['network']['segmentResults']:
            if verbose: generate_progress_bar(count, 6903, "{0} of {1} ({2}%)".format(count, 6903, round(count*100/6903, 1)))

            self.add_elements(tt_segment=segment)
            count += 1

        # The TOMTOM network is more complex than the OpenStreetMap
        # data, so degree 2 nodes are removed.
        self.simplify()

    def build_from_query(self, query, verbose):
        """
        Builds network with data from OpenStreetMap, using a query
        to Overpass API.
        :param query:   Overpass API query
        :param verbose: Print network creation progress
        """

        overpy_api = overpy.Overpass()
        result = ""

        while result == "":
            try:
                if verbose: print("   ... Querying Overpass API.")
                result = overpy_api.query(query)

            # If the Overpass API server is overloaded or has received
            # too many requests, the program times out before retrying.
            except overpy.exception.OverpassTooManyRequests:
                if verbose: print("         ↳ Too many requests, sleeping for 10s...")
                sleep(10)

            except overpy.exception.OverpassGatewayTimeout:
                if verbose: print("         ↳ Server overloaded, sleeping for 20s...")
                sleep(20)

        segments = result.get_ways()
        nodes = result.get_nodes()
        no_segments = len(segments)

        if verbose: print('   ... Query successful: Returned {0} ways, {1} nodes.'.format(no_segments, len(nodes)))

        count = 1

        for segment in segments:
            added = False
            while added == False:
                try:
                    if verbose: generate_progress_bar(count, no_segments, "{0} of {1} ({2}%)".format(count, no_segments, round(count*100/no_segments, 1)))

                    # Each segment is added with the add_elements function.
                    self.add_elements(osm_segment=segment)
                    added = True
                    count += 1

                # The details of each  node has to be fetched from Overpass API,
                # so the same timeout rules are applied here as well.
                except overpy.exception.OverpassTooManyRequests:
                    if verbose: generate_progress_bar(count, no_segments, 'Sleeping for 10s...    ')
                    sleep(10)
                    
                except overpy.exception.OverpassGatewayTimeout:
                    if verbose: generate_progress_bar(count, no_segments, 'Sleeping for 20s...    ')
                    sleep(20)
                
    def add_elements(self, osm_segment=None, tt_segment=None):
        """
        Adds segments to the current network object, as well as
        any of its connecting nodes.
        :param osm_segment: Overpy way object from query result
        :param tt_segment:  TOMTOM data segment
        """

        # Both the OSM and TT networks use the same function for
        # creating nodes and segments.
        if osm_segment != None and tt_segment == None:
        
            segment_nodes = osm_segment.get_nodes(resolve_missing=True)

            # The coordinates and keys of all of a segment's nodes are
            # stored, for drawing and finding connected segments respectively.
            nodes_arr = []
            coors_arr = []
            for node in segment_nodes:
                if node.id not in self.nodes:
                    node_obj = Node(float(node.lat), float(node.lon))
                    self.nodes[node.id] = node_obj
                    coors_arr.append(node_obj.get_coors())

                else: coors_arr.append(self.nodes[node.id].get_coors())
                    
                nodes_arr.append(node.id)
                self.nodes[node.id].attach_segment(osm_segment.id)

            if osm_segment.id not in self.segments:
                # OpenStreetMap properties are stored in an attributes dictionary,
                # such as the street name, speed limit, number of lanes etc.
                data = format_osm_data(osm_segment)
                self.segments[osm_segment.id] = Segment(nodes_arr, coors_arr, attributes=data)
                self.segments[osm_segment.id].calculate_length()

        elif osm_segment == None and tt_segment != None:
            tt_segment_id = abs(int(tt_segment['segmentId']))

            nodes_arr = []
            coors_arr = []
            for coor in tt_segment['shape']:

                # The TOMTOM network does not contain node objects, instead solely using
                # the coordinates associated with each segment, and so do not have keys. So,
                # for the nodes dictionary, a unique key is generated by multiplying the 
                # longitude and latitude values for each node.
                node_id = int(abs(coor['latitude']*coor['longitude'])*(10**12))
                if node_id not in self.nodes:
                    node_obj = Node(float(coor['latitude']), float(coor['longitude']))
                    self.nodes[node_id] = node_obj
                    coors_arr.append(node_obj.get_coors())

                else: coors_arr.append(self.nodes[node_id].get_coors())

                nodes_arr.append(node_id)
                self.nodes[node_id].attach_segment(tt_segment_id)

            if  tt_segment_id not in self.segments:
                # The flow data is formatted and added to the segment's attribute dictionary.
                attributes = format_tt_data(tt_segment)
                self.segments[tt_segment_id] = Segment(nodes_arr, coors_arr, attributes=attributes)

    def simplify(self):
        """
        Joins together all segments where one road consists of
        multiple segments by removing degree 2 nodes.
        """
        for node_id in self.nodes:
            segments = self.nodes[node_id].get_attached()
            if len(segments) == 2:
                
                segment0 = self.segments[segments[0]]
                segment1 = self.segments[segments[1]]

                # Segments are only joined if they share a degree 2 node at either end, and
                # they have the same street name.
                if segment0.get_attributes()['streetName'] == segment1.get_attributes()['streetName']:
                    new_attributes = merge_flow_data(segment0, segment1)
                    if node_id == segment0.get_nodes()[-1] and node_id == segment1.get_nodes()[0]:

                        new_segment = segment0.join_segment(segment1, new_attributes)
                        self.replace_segments(segments[0], segments[1], new_segment)

                    if node_id == segment0.get_nodes()[0] and node_id == segment1.get_nodes()[-1]:
                        new_segment = segment1.join_segment(segment0, new_attributes)
                        self.replace_segments(segments[0], segments[1], new_segment)

    def replace_segments(self, id1, id2, replacement=None):
        """
        Replaces one segment in the network with one new segment.
        :param id1:         ID of first segment to replace
        :param id2:         ID of second segment to replace
        :param replacement: New segment.
        """

        # A unique ID is created for the new segment by adding together
        # the original segments' IDs.
        replacement_id = int(abs(sum(replacement.get_coors()[0])) + abs(sum(replacement.get_coors()[1]))*(10**5))
        new_segment_dict = self.segments.copy()

        # The segment dictionary is iterated through, and the original
        # segments are deleted once a match is found.
        deleted1 = False
        deleted2 = False
        for segment_id in new_segment_dict:
            if not deleted1 and segment_id == id1:
                self.segments.pop(id1)
                deleted1 = True
            if not deleted2 and segment_id == id2:
                self.segments.pop(id2)
                deleted2 = True
            if deleted1 and deleted2:
                break

        # The new replacement segment's ID is added to the attached_segments
        # of all of its nodes.
        if replacement_id != None:
            for node in self.nodes.values():
                attached = node.get_attached()
                if id1 in attached:
                    node.set_attached([replacement_id if x==id1 else x for x in attached])
                    replaced1 = True
                if id2 in attached:
                    node.set_attached([replacement_id if x==id2 else x for x in attached])
                    replaced2 = True
        
        self.segments[replacement_id] = replacement
    
    def build_KDTree(self, end_nodes=False):
        """
        Builds K-D tree of all the network's nodes.
        :param end_nodes: restrict K-D tree to nodes at the end of segments
        :return [int]:    array of node keys
        :return KDTree:   K-D Tree object
        """
        node_keys = []
        node_coors = []
        for key in self.nodes.keys():
            if end_nodes:
                if self.is_end_node(key) == False:
                    continue
            node_keys.append(key)
            node_coors.append(self.nodes[key].get_coors())

        node_coors = np.asarray(node_coors)

        kdt = KDTree(node_coors)

        # Returns an ordered list of node keys so the data can be
        # fetched with the node's indices.
        return node_keys, kdt

    def merge_with_network(self, network):
        """
        Merges the current network with another.
        :param network: network to merge with
        """

        # Any segments shared by the two networks are only represented once.
        for key in network.get_network_segments().keys():
            if key not in self.segments:
                self.segments[key] = network.get_network_segments()[key]

        for key in network.get_network_nodes().keys():
            if key not in self.nodes:
                self.nodes[key] = network.get_network_nodes()[key]

    def calculate_factors(self, get_highest_speed=False, get_highest_emissions=False):
        """
        Calculates average network speed, emissions and average flow rate.
        Also finds the most congested and highest emitting segment, and can
        return either the highest average speed or emissions value (for calculating
        boundaries when drawing the network).
        :param get_highest_speed:     whether to return the highest speed
        :param get_highest_emissions: whether to return the highest emissions
        :return most_congested:       key of the most congested segment
        :return worst_emitter:        key of the highest emitting segment
        :return worst_emissions:      highest average emissions
        :return highest_av_speed:     highest average speed
        """
        no_segments = len(self.segments)

        # The average hourly speeds, emissions and flow are calculated.
        av_speed = [0]*12
        av_emis = [0]*12
        av_vph = [0]*12

        worst_spi = math.inf
        worst_emissions = 0
        most_congested = 0
        worst_emitter = 0

        highest_av_speed = 0

        for key in self.segments.keys():
            segment = self.segments[key]
            attributes = segment.get_attributes()

            speeds = segment.get_flow_measures(1)
            emissions = attributes['emissions']
            vphs = segment.get_flow_measures(3)

            for i in range(12):
                
                av_speed[i] += speeds[i]
                av_emis[i] += emissions[i]
                av_vph[i] += vphs[i]

            # The worst emitter is calculated using their average emissions
            # value throughout the day.
            if sum(emissions)/len(emissions) != 0 and sum(emissions)/len(emissions) > worst_emissions:
                worst_emitter = key
                worst_emissions = sum(emissions)/len(emissions)

            # The most congested segment is found using speed performance index (SPI),
            # ie. how fast the average speed is compared to the free-flow speed, or speed limit.
            if sum(segment.get_flow_measures(3)) / len(segment.get_flow_measures(3)) >= 100 and attributes['speedLimit'] != 'unknown':

                speedLimit = int(attributes['speedLimit'].split()[0])*1.609344

                spi = (sum(segment.get_flow_measures(1)) / len(segment.get_flow_measures(1)))/speedLimit*100
                
                if spi < worst_spi:
                    most_congested = key
                    worst_spi = (sum(segment.get_flow_measures(1)) / len(segment.get_flow_measures(1)))/speedLimit*100

            if sum(segment.get_flow_measures(1)) / len(segment.get_flow_measures(1)) >= highest_av_speed:
                highest_av_speed = sum(segment.get_flow_measures(1)) / len(segment.get_flow_measures(1))
                
        self.av_speed = [round(x / no_segments, 2) for x in av_speed]
        self.av_emissions = [round(x / no_segments, 2) for x in av_emis]
        self.av_vph = [round(x / no_segments, 2) for x in av_vph]

        if get_highest_emissions:
            return most_congested, worst_emitter, worst_emissions
        elif get_highest_speed:
            return most_congested, worst_emitter, highest_av_speed
        else:
            return most_congested, worst_emitter


    def export_network(self, segment_output="segments.csv", node_output="nodes.csv", flow_output="flow.csv", emissions_output="emissions.csv", zip_output="network.zip"):
        """
        Exports the network data as a zip file.
        :param segment_output:   segment output filename
        :param node_output:      node output filename
        :param flow_output:      flow data output filename
        :param emissions_output: emissions data output filename
        :param zip_output:       final zip filename
        """
        segment_file = open(CSV_DIR+segment_output, 'w')
        flow_file = open(CSV_DIR+flow_output, 'w')
        emissions_file = open(CSV_DIR+emissions_output, 'w')

        segment_file.write('segment_key,start_node,end_node,street_name,road_type,no_lanes,speed_limit,oneway,width,two_wheeled_vehicles,passenger_cars,buses_coaches,lgvs,hgvs')
        flow_header = ""
        emissions_header = ""

        # All hourly flow & emissions data is printed in separate columns.
        for i in range(6, 18):
            flow_header += '{0}_average_speed,{0}_median_speed,{0}_flow,'.format(i)
            emissions_header += str(i)+","

        flow_file.write(flow_header[:-1])
        emissions_file.write(emissions_header[:-1])

        for key in self.segments.keys():
            segment = self.segments[key]
            attributes = segment.get_attributes()
            start_node = segment.get_nodes()[0]
            end_node = segment.get_nodes()[-1]

            # All of a segment's attributes dictionary is printed to the final file
            # so it can be reconstructed later.
            segment_file.write('\n{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13}'.format(key, start_node, end_node,
                                                                                                        attributes['streetName'],
                                                                                                        attributes['roadType'],
                                                                                                        attributes['noLanes'],
                                                                                                        attributes['speedLimit'],
                                                                                                        attributes['oneway'],
                                                                                                        attributes['width'],
                                                                                                        attributes['vehicleProps'][0],
                                                                                                        attributes['vehicleProps'][1],
                                                                                                        attributes['vehicleProps'][2],
                                                                                                        attributes['vehicleProps'][3],
                                                                                                        attributes['vehicleProps'][4]))

            if 'flowData' in attributes:
                flow_str = "\n"
                for time_slot in attributes['flowData']:
                    flow_str += '{0},{1},{2},'.format(time_slot[1], time_slot[2], time_slot[3])
                flow_file.write(flow_str[:-1])

            if 'emissions' in attributes:
                emissions_str = "\n"
                for time_slot in attributes['emissions']:
                    emissions_str += str(time_slot)+","
                emissions_file.write(emissions_str[:-1])
        
        with open(CSV_DIR+node_output, 'w') as node_file:
            
            # Only the node coordinates are printed for the node file.
            node_file.write('key,latitude,longitude')
            for key in self.nodes.keys():
                node = self.nodes[key]
                node_file.write('\n{0},{1},{2}'.format(key, node.get_coors()[0], node.get_coors()[1]))

        with ZipFile(ZIP_DIR+zip_output, 'w') as zip_file:
            for folder_name, _, _ in os.walk(CSV_DIR):
                for output_file in [segment_output, node_output, flow_output, emissions_output]:
                    file_path = os.path.join(folder_name, output_file)
                    zip_file.write(file_path, basename(file_path))

        return ZIP_DIR+zip_output

    def is_end_node(self, key):
        """
        Finds whether or not the node is an end node.
        :param key:   node key
        :return bool: denotes whether the node is an end node
        """
        node = self.nodes[key]
        segments = node.get_attached()
        for segment_id in segments:
            segment = self.segments[segment_id]
            nodes = segment.get_nodes()
            if key == nodes[0] or key == nodes[-1]:
                return True
        return False

    def open_road(self, key):
        """
        Opens a road segment.
        :param key: segment to open
        """
        segment = self.segments[key]
        segment.closed = not segment.closed

    def is_closed(self, key):
        return self.segments[key].closed

    def get_network_segments(self):
        return self.segments

    def get_network_nodes(self):
        return self.nodes

    def get_av_emissions(self):
        return self.av_emissions
    
    def get_av_speed(self):
        return self.av_speed

    def get_av_vph(self):
        return self.av_vph

class Node:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.attached_segments = []

    def attach_segment(self, segment_id):
        """
        Adds a segment ID to a node's attached array.
        :param segment_id: segment to attach
        """
        if segment_id not in self.attached_segments:
            self.attached_segments.append(segment_id)

    def get_attached(self):
        return self.attached_segments
    
    def set_attached(self, attached):
        self.attached_segments = attached

    def get_coors(self):
        return [self.lat, self.lon]

    def __str__(self):
        return str(self.__class__) + ": coors=" + str(self.get_coors())

class Segment:
    def __init__(self, nodes, coors, attributes=None):
        self.nodes = nodes
        self.coors = coors
        self.closed = False
        self.attributes = attributes

    def join_segment(self, joining_segment, attributes):
        """
        Creates a new segment by attaching one to the end of the
        current segment. Neither original segment is changed.
        :param joining_segment: Appending segment
        :return Segment:        Resulting segment object
        """
        new_nodes = self.nodes + joining_segment.get_nodes()[1:]
        new_coors = self.coors + joining_segment.get_coors()[1:]

        new_segment = Segment(new_nodes, new_coors, attributes=attributes)
        new_segment.calculate_length()

        return new_segment

    def calculate_length(self):
        """
        Calculates the length of a segment and stores the result
        in its attribute dictionary.
        """
        length = 0
        for i in range(len(self.coors) - 1):
            length += distance(self.coors[i], self.coors[i+1]).km
        self.attributes['length'] = length

        long_av = 0
        lat_av = 0
        for coor in self.coors:
            long_av += coor[0]
            lat_av += coor[1]
        
        # The coordinates of the segment's centre is also
        # calculated and stored.
        self.attributes['centre'] = [long_av / len(self.coors), lat_av / len(self.coors)]

    def get_flow_measures(self, index):
        """
        Returns a specific column from the flow data, representing
        that measure's values over the course of a day.
        """
        return [i[index] for i in self.get_attributes()['flowData']]

    def set_flow_measure(self, val, time_index, val_index):
        self.attributes['flowData'][time_index][val_index] = val

    def set_attribute(self, key, data):
        self.attributes[key] = data
                
    def set_attributes(self, attributes):
        self.attributes = attributes

    def get_nodes(self):
        return self.nodes

    def get_coors(self):
        return self.coors

    def get_attributes(self):
        return self.attributes

    def __str__(self):
        return str(self.__class__) + ": name='" + self.attributes['streetName']+"'"

def format_tt_data(segment):
    """
    Creates a dictionary of TOMTOM flow data for the
    given segment.
    :param segment: Specified segment
    :return dict:   Dictionary of flow data
    """
    attributes = {}
    flow_data = []
    if 'streetName' in segment:
        attributes['streetName'] = segment['streetName']
    else: attributes['streetName'] = 'unnamed'
    
    for time_slot in segment['segmentTimeResults']:
        flow_data.append([time_slot['timeSet'] + 4,
                          round(time_slot['averageSpeed'], 2),
                          round(time_slot['medianSpeed'], 2),
                          round(time_slot['sampleSize'], 2)])

    attributes['flowData'] = flow_data
    
    return attributes

def format_osm_data(segment):
    """
    Creates a dictionary of road attributes from OpenStreetMap
    data.
    :param segment: Specified segment
    :return dict:   Dictionary of segment attributes
    """
    popup, tooltip = format_popup_tooltip(segment)
    
    attributes = {}

    # An 'unknown' value is always stored in place of the actual value
    # in order to reduce KeyErrors when accessing the dictionary.
    if 'name' in segment.tags:
        attributes['streetName'] = segment.tags['name']
    else: attributes['streetName'] = 'unnamed'

    if 'highway'  in segment.tags:
        attributes['roadType']   = segment.tags['highway']
    else: attributes['roadType'] = 'unclassified'

    estimate = False
    if 'lanes'    in segment.tags:
        try: attributes['noLanes']    = int(segment.tags['lanes'])
        except ValueError: estimate = True
    else: estimate = True

    # If the OpenStreetMap does not store the number of lanes, it is estimated
    # based on the road type.
    if estimate:
        if   attributes['roadType'] == 'motorway':     attributes['noLanes'] = 6
        elif attributes['roadType'] == 'trunk':        attributes['noLanes'] = 4
        elif attributes['roadType'] == 'primary':      attributes['noLanes'] = 4
        elif attributes['roadType'] == 'secondary':    attributes['noLanes'] = 4
        elif attributes['roadType'] == 'tertiary':     attributes['noLanes'] = 2
        elif attributes['roadType'] == 'unclassified': attributes['noLanes'] = 2
        elif attributes['roadType'] == 'residential':  attributes['noLanes'] = 2
        else:                                          attributes['noLanes'] = 2

    if 'maxspeed' in segment.tags:
        attributes['speedLimit'] = segment.tags['maxspeed']
    else: attributes['speedLimit'] = 'unknown'

    if 'oneway'   in segment.tags:
        attributes['oneway']     = segment.tags['oneway']
    else: attributes['oneway'] = 'unknown'

    if 'width'    in segment.tags:
        attributes['width']      = segment.tags['width']
    else: attributes['width'] = 'unknown'

    attributes['popup']      = popup
    attributes['tooltip']    = tooltip

    return attributes

def format_popup_tooltip(segment):
    """
    Formats a generic popup and tooltip data for the given segment
    with HTML tags.
    :param segment: Overpy segment
    :return string: Popup message
    :return string: Tooltip message
    """
    info = ['highway','maxspeed','oneway']
    popup = ""

    if 'name' in segment.tags.keys():
        tooltip = '<b>'+segment.tags['name']+'</b>'
        popup = '<u><b>'+segment.tags['name']+'</b></u></br>'
    else:
        tooltip = 'unamed'

    for tag in info:
        if tag in segment.tags.keys():
            popup = popup+tag+"="+segment.tags[tag]+'</br>'
    
    return popup, tooltip

def merge_flow_data(segment1, segment2):
    """
    Merges flow data values for two segments.
    :param segment1: Segment to merge
    :param segment2: Segment to merge
    :return dict:    Merged dictionary
    """
    seg1 = segment1.get_attributes()['flowData']
    seg2 = segment2.get_attributes()['flowData']
    
    new_seg_attributes = {}
    new_seg_attributes['streetName'] = segment1.get_attributes()['streetName']

    new_flow_data = []
    for i in range(len(seg1)):
        if seg1[i][3] > 0 and seg2[i][3] >0:
            # Averages are found for the average and median speed, whilst flow rate
            # simply uses the maximum value from the two segments.
            new_flow_data.append([seg1[i][0], # time
                                  round(((seg1[i][1]*seg1[i][3])+(seg2[i][1]*seg2[i][3]))/(seg1[i][3]+seg2[i][3]), 2), # average speed
                                  round((seg1[i][2]+seg2[i][2])/2, 2), # average median speed
                                  (max(seg1[i][3], seg2[i][3]))]) # Flow rate
        elif seg1[i][3] > 0 and seg2[i][3] == 0:
            new_flow_data.append(seg1[i])
        elif seg1[i][3] == 0 and seg2[i][3] > 0:
            new_flow_data.append(seg2[i])
        elif seg1[i] == seg2[i]:
            new_flow_data.append(seg1[i])

    new_seg_attributes['flowData'] = new_flow_data

    return new_seg_attributes

def generate_progress_bar (count, no_segments, state, bar_length = 20, fill = '█', empty='-', prefix='   ... Adding segments:  '):
    """
    Prints a progress bar to the console.
    :param count:       current value
    :param no_segments: maximum value
    :param state:       message printed next to the progress bar
    :param bar_length:  bar dimension
    :param fill:        filled bar characters
    :param empty:       empty bar characters
    :param prefix:      message printed before the progress bar
    """
    filledLength = int(bar_length * count // no_segments)
    bar = fill * filledLength + empty * (bar_length - filledLength)
    bar = (f'|{bar}|')

    sys.stdout.write("\r"+prefix+"{0} {1}".format(bar, state))
    sys.stdout.flush()