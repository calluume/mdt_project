import sys, folium, random, pickle
from time import time
from folium.raster_layers import TileLayer

from . import Network

labels = ['outline', '6:00 - 7:00', '7:00 - 8:00', '8:00 - 9:00', '9:00 - 10:00', '10:00 - 11:00', '11:00 - 12:00', '12:00 - 13:00', '13:00 - 14:00', '14:00 - 15:00', '15:00 - 16:00', '16:00 - 17:00', '17:00 - 18:00']

# Tiles: https://leaflet-extras.github.io/leaflet-providers/preview/
CartoDB_PositronNoLabels = 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png'
CartoDB_VoyagerNoLabels = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png'

class FoliumMap():
    def __init__(self, location=[53.480432336847954, -2.2426423001611924], style=CartoDB_VoyagerNoLabels, zoom_start=13.5, layer_labels=labels):
        """
        Creates a FoliumMap object.
        :param location:     map central coordinates
        :param style:        basemap style link
        :param zoom_start:   initial map zoom level
        :param layer_labels: map layer labels
        """
        
        self.location = location
        self.zoom_start=zoom_start
    
        self.fig = folium.Figure(width="100%", height=520)

        self.map = folium.Map(location=self.location,
                              zoom_start=self.zoom_start,
                              tiles=None,
                              width='100%',
                              height='100%',
                              scrollWheelZoom=True).add_to(self.fig)

        folium.TileLayer(style, name='OSM Map', attr='https://www.openstreetmap.org/copyright', min_zoom=13, overlay=True, control=False).add_to(self.map)

        self.osm_layer = folium.FeatureGroup('OpenStreetMap')
        self.tt_layer = folium.FeatureGroup('TOMTOM')

        # Layers are created from the labels given, and are stored in
        # an array.
        self.layers = []
        for label in layer_labels:
            self.layers.append(folium.FeatureGroup(label, overlay=False, control=(label!='outline'), show=(label==layer_labels[1])))

        self.seg_attributes = {}

    def draw_segment(self, layer, coors, weight=5, colour='random', popup=None, tooltip=None):
        """
        Draws a segment onto the map.
        :param layer:   Folium layer index
        :param coors:   List of segment coors
        :param weight:  Segment line weight
        :param colour:  Segment line colour
        :param popup:   Segment popup message
        :param tooltip: Segment tooltip message
        """

        line = folium.vector_layers.PolyLine(coors, weight=weight, color=colour, popup=popup, tooltip=tooltip)
        line.add_to(self.layers[layer])

    def draw_network(self, network, metric=None, weight=5, lower_bounds=0, upper_bounds=1, draw_zero_values=True, seg_limit=None, time_segments=12, verbose=False):
        """
        Draws all network segments onto folium map with an outline
        and all time slots on their respective layers.
        :param network:          network object to draw
        :param metric:           metric to be drawn on the map, either 'flow' or 'emissions'
        :param weight:           segment line weight
        :param lower_bounds:     segments with average values below are not drawn
        :param upper_bounds:     segments with average values above are not drawn
        :param draw_zero_values: segments with an average value of 0 are ignored
        :param seg_limit:        limits the amount of drawn segments
        :param time_segments:    amount of hours added to the map
        :param verbose:          print render progress
        """
        if verbose: print("Drawing '{0}' network:".format(metric))
        segments = network.get_network_segments()

        # The segment limit simply draws the first n segments in the dictionary.
        if seg_limit != None:
            segments = {k: segments[k] for k in list(segments)[:seg_limit]}

        count = 1
        for key in segments.keys():

            if verbose: sys.stdout.write("\r   ... Drawing segment:   {0} of {1}".format(count, len(segments.keys())))
            if verbose: sys.stdout.flush()

            segment = segments[key]
            attributes = segment.get_attributes()
            self.seg_attributes[key] = attributes
            if metric != None:

                # Values and colour values are set before the segments are drawn.
                if metric == 'flow':
                    segment_data = segment.get_flow_measures(2)
                    colour_params = [[5, 50], [(255, 15, 15), (255, 255, 0), (0, 255, 0)]]
                elif metric == 'emissions':
                    segment_data = attributes['emissions']
                    colour_params = [[0, 1000], [(0, 0, 255), (0, 255, 255), (0, 255, 0), (255, 255, 0), (255, 0, 0)]]
                
                # If the average value is outside the boundaries, or has a zero value (with draw_zero_values=True)
                # the segment is ignored.
                av_val = sum(segment_data) / len(segment_data)
                if av_val < lower_bounds or av_val > upper_bounds or (av_val == 0 and not draw_zero_values): continue

                # An outline is drawn on the bottom layer.
                self.draw_segment(0, segment.get_coors(), colour='black', weight=weight+1)
                for i in range(1, time_segments+1):
                    colours = generate_colours(segment_data, colour_params[0], colour_params[1])
                    self.draw_segment(i, segment.get_coors(), colour=colours[i-1], weight=weight, popup=generate_popup(key, street_name=attributes['streetName']), tooltip=attributes['tooltip'])

            count += 1

        if verbose: print('\n   ... Rendering.')

    def draw_generic(self, network, colour='#6cb165', weight=5, b_outline=True, w_outline=False, save=None, verbose=False):
        """
        Draws a generic map, for displaying a network without a metric. If a
        save name is not given, the map is returned in a html format.
        :param network:   network object to be drawn
        :param colour:    colour for all segments
        :param weight:    segment line weight
        :param b_outline: denotes a black outline should be drawn
        :param w_outline: denotes a white outline should be drawn
        :param save:      the html file to save the map to
        :param verbose:   print map drawing progress
        """
        segments = network.get_network_segments()

        count = 1
        for key in segments.keys():
            segment = segments[key]
            if verbose: sys.stdout.write("\r   ... Drawing segment:   {0} of {1}".format(count, len(segments.keys())))
            if verbose: sys.stdout.flush()

            if b_outline:
                self.draw_segment(0, segment.get_coors(), colour='black', weight=weight+1)
            elif w_outline:
                self.draw_segment(0, segment.get_coors(), colour='white', weight=weight+1)

            self.draw_segment(1, segment.get_coors(), weight=weight, colour=colour)
            count += 1

        if verbose: print('\n   ... Rendering.')
        self.add_time_layers()

        if save != None:
            self.map.save(save)
            if verbose: print('Saved to \''+save+"'")
        else: return self.map._repr_html_()

    def add_time_layers(self):
        """
        Applies all map layers and adds layer control.
        """
        for layer in self.layers:
            layer.add_to(self.map)

        folium.LayerControl(position='topleft', collapsed=True).add_to(self.map)
    
    def get_map(self):
        return self.map._repr_html_()

    def seg_exists(self, key):
        return (key in self.seg_attributes)

    def get_seg_attributes(self, key):
        return self.seg_attributes[key]

def generate_popup(key, street_name='Segment'):    
    script = "<button onclick=\"parent.inspect("+str(key)+")\">Inspect <i>"+street_name+"</i></button>"

    html = folium.Html(script, script=True)
    popup = folium.Popup(html, max_width=2650)
    return popup

def generate_colours(values, val_range, colour_range, no_val='#9c9c9c'):
    """
    Maps flow data to list of hex codes, corresponding to the
    given colour scale.
    :param values:       flow data values
    :param val_range:    list containing upper and lower limits for applying colours
    :param colour_range: list of tuples containing RGB colour values
    :param no_val:       hex code for representing a 0 value.
    :return [str]:       list of hex codes.
    """
    colours = []
    range_width = 1/(len(colour_range) - 1)
    for value in values:

        if value == 0:
            colours.append(no_val)
        
        # If a segment is out of the val_range, the segment is given
        # the max or min colour values.
        elif value >= val_range[-1]:
            colours.append('#%02x%02x%02x' % (colour_range[-1][0], colour_range[-1][1], colour_range[-1][2]))
        elif value <= val_range[0]:
            colours.append('#%02x%02x%02x' % (colour_range[0][0], colour_range[0][1], colour_range[0][2]))
        else:
            percent = (value/val_range[-1])

            start_colour_index = int(percent // range_width)
            start_colour = colour_range[start_colour_index]
            end_colour = colour_range[start_colour_index+1]
            
            percent = percent % range_width

            # The RGB values are calculated by interpolating between the
            # colour range.
            red = end_colour[0] - start_colour[0]
            green = end_colour[1] - start_colour[1]
            blue = end_colour[2] - start_colour[2]
            
            colours.append('#%02x%02x%02x' % (start_colour[0]+int(red*percent),
                                              (start_colour[1]+int(green*percent)),
                                              (start_colour[2]+int(blue*percent))))
    return colours