import folium
from math import modf
import plotly.offline as opy
import plotly.graph_objs as go

from django import template

register = template.Library()
times = ['6:00', '7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']

@register.simple_tag(takes_context=True)
def get_attributes(context, seg_key):
    """
    Formats a segment's attributes array into a readable table.
    :param seg_key:  specified segment ID
    :return [[str]]: formatted, zipped arrays
    """
    if 'my_map' in context:
        all_attributes = context['my_map'].get_seg_attributes(seg_key)
    elif 'network' in context:
        all_attributes = context['network'].get_network_segments()[seg_key].get_attributes()

    length = all_attributes['length']
    width = all_attributes['width']

    if all_attributes['speedLimit'] == 'unknown': speedLimit = 'Unknown'
    else: speedLimit = all_attributes['speedLimit'].replace(" ", "")

    attributes = [all_attributes['roadType'].replace("_", " ").title(), speedLimit,
                  str(all_attributes['noLanes']).title(), format_distance(all_attributes['length']), format_distance(all_attributes['width']),
                  all_attributes['oneway'].title(), format_coors(all_attributes['centre'])]
    
    headers = ["Road Classification", "Speed Limit", "No. of Lanes", "(Segment) Length", "Width", "Oneway Road", "Road Coordinates"]
    return zip(headers, attributes)

@register.simple_tag(takes_context=True)
def get_seg_data(context, seg_key):
    """
    Formats segment emissions and flow data into a table.
    :param seg_key:  segment key
    :return [[str]]: formatted, zipped arrays
    """
    if 'my_map' in context:
        attributes = context['my_map'].get_seg_attributes(seg_key)
    elif 'network' in context:
        attributes = context['network'].get_network_segments()[seg_key].get_attributes()

    speeds = zip(times, [round(i[2],2) for i in attributes['flowData']])
    emissions = zip(times, [round(x, 2) for x in attributes['emissions']])
    flow = zip(times, [round(i[3], 2) for i in attributes['flowData']])

    emissions = [["rd-em", "Hourly CO<sub>2</sub> Emissions", "Times", "CO<sub>2</sub> Emissions (g)"], emissions]
    speeds = [["rd-sp", "Hourly Average Speeds", "Times", "Average Speed (mph)"], speeds]
    flow = [["rd-fl", "Hourly Flow Rate", "Times", "No. of Vehicles per Hour"], flow]

    if 'metric' in context:
        if context['metric'] == 'Emissions':
            return [emissions, flow]
        
    return [flow, speeds, emissions]

@register.simple_tag(takes_context=True)
def get_minimap(context, seg_key):
    """
    Creates a minimap surrounding a given segment.
    :param seg_key: segment key
    :return div:    folium map div
    """
    if 'my_map' in context:
        attributes = context['my_map'].get_seg_attributes(seg_key)
    elif 'network' in context:
        attributes = context['network'].get_network_segments()[seg_key].get_attributes()

    coors = attributes['centre']

    fig = folium.Figure(width='100%', height=150)

    mm = folium.Map(location=coors,
                    zoom_start=15,
                    tiles=None,
                    width='100%',
                    height='100%',
                    scrollWheelZoom=False,
                    control_scale=False,
                    no_touch=True,
                    zoom_control=False,
                    dragging=False).add_to(fig)

    folium.TileLayer('https://{s}.tile.jawg.io/jawg-terrain/{z}/{x}/{y}{r}.png?access-token=Iydi3j8ktAlcBWqZYvlzbNZy7zOOTn14kckZVLfE8pIQWept3aoVRP9xIP6E7u7y',
                     name='OSM Map',
                     attr='<a href="http://jawg.io" title="Tiles Courtesy of Jawg Maps" target="_blank">&copy; <b>Jawg</b>Maps</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                     overlay=True,
                     control=False).add_to(mm)

    folium.Marker(location=coors, 
                  icon=folium.Icon(color="green",
                                   icon="circle",
                                   prefix='fa')
                 ).add_to(mm)

    return mm._repr_html_()

@register.simple_tag(takes_context=True)
def get_seg_graph(context, seg_key, metric):
    """
    Creates a barchart for a specified metric on a given
    segment.
    :param seg_key: segment key
    :param metric:  either 'Emissions' or 'Flow'
    :return div:    plotly barchart div
    """
    if 'my_map' in context:
        attributes = context['my_map'].get_seg_attributes(seg_key)
    elif 'network' in context:
        attributes = context['network'].get_network_segments()[seg_key].get_attributes()
        
    if metric == 'Emissions':
        y = attributes['emissions']
        colour = '#6cb165'
        title = 'Hourly CO<sub>2</sub> Emissions for <i>'+attributes['streetName']+"</i> (g)"

    if metric == 'Flow':
        y = [i[3] for i in attributes['flowData']]
        colour = '#4c66ba'
        title = 'Hourly Flow Rate for <i>'+attributes['streetName']+'</i>'
        metric = 'flow rate'

    if sum(y)/len(y) != 0:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=times,
                            y=y,
                            marker_color=colour))
        fig.update_layout(
            plot_bgcolor='rgb(244,244,244)',
            barmode='group',
            title=dict(text=title, x=0.5, font_size=15),
            xaxis_title='Hour',
            margin=dict(r=40, l=60, t=40, b=50),
            autosize=True,
            height=300,
            hovermode="x unified",
            hoverlabel=dict(bordercolor='white', bgcolor='rgb(244,244,244)', font=dict(color='#9c9c9c'))
        )

        return opy.plot(fig, auto_open=False, output_type='div')
    else:
        return "<div class='not-enough'><h2>Not enough data to display "+metric.lower()+".</h2></div>"

@register.simple_tag(takes_context=True)
def get_vehicle_pie(context, seg_key):
    """
    Creates a vehicle distribution piechart for a specified
    segment.
    :param seg_key: segment key
    :return div:    plotly piechart div
    """
    if 'my_map' in context:
        attributes = context['my_map'].get_seg_attributes(seg_key)
    elif 'network' in context:
        attributes = context['network'].get_network_segments()[seg_key].get_attributes()

    labels = ['Mopeds & Motorcycles','Passenger Cars & Taxis','Buses & Coaches','LGVs', 'HGVs']
    vehicle_type_prop = attributes['vehicleProps']

    if 'type_props' in context:
        type_props = context['type_props']
        if len(type_props) == len(vehicle_type_prop):
            vehicle_type_prop = [a*b for a,b in zip(vehicle_type_prop,type_props)]

        if sum(vehicle_type_prop) != 0:
            fig = go.Figure(data=[go.Pie(labels=labels,
                                        values=vehicle_type_prop,
                                        texttemplate="%{percent}")])

            fig.update_traces(hoverinfo='label+percent',
                            textinfo='value')
            fig.update_layout(
                margin=dict(r=40, l=60, t=40, b=50),
                autosize=True,
                height=300,
                hovermode="x unified",
                hoverlabel=dict(bordercolor='white', bgcolor='rgb(244,244,244)', font=dict(color='#9c9c9c'))
            )
            return opy.plot(fig, auto_open=False, output_type='div')
    
    return "<div class='not-enough'><h2>Not enough data to display proportions.</h2></div>"

@register.simple_tag(takes_context=True)
def get_name(context, seg_key):
    """
    Returns a segment's name from its key.
    :param seg_key: segment key
    :return str:    segment street name
    """
    if 'my_map' in context:
        fol = context['my_map']
        return fol.get_seg_attributes(seg_key)['streetName']
    else:
        return context['network'].get_network_segments()[seg_key].get_attributes()['streetName']

@register.simple_tag(takes_context=True)
def get_flow_data(context, seg_key):
    fol = context['my_map']
    return fol.get_seg_attributes(seg_key)['flowData']

@register.simple_tag(takes_context=True)
def get_emissions(context, seg_key):
    fol = context['my_map']
    return zip("el", times, fol.get_seg_attributes(seg_key)['emissions'])

@register.simple_tag(takes_context=True)
def exists(context, seg_key):
    fol = context['my_map']
    return fol.seg_exists(seg_key)

@register.simple_tag(takes_context=True)
def diesel_prop(context, seg_key):
    return round(100 - context['modifiers'][0], 1)

@register.simple_tag(takes_context=True)
def get_map(context):
    fol = context['my_map']
    return fol.get_map()

def format_distance(distance_str):
    """
    Formats distance value by adding km/m units.
    :param distance_str: distance value as a string
    """
    if distance_str != 'unknown':
        value = float(distance_str)
        if value > 1:
            return str(round(value, 2))+"km"
        else:
            value *= 1000
            return str(round(value, 2))+"m"
    else:
        return distance_str.title()

def format_coors(coors):
    """
    Formats a coordinate pair into full sexagesimal format,
    with N/E/S/W characters.
    :param coors: latitude, longitude coordinates array
    :return str:  formatted coordinate string
    """
    if coors[0] > 0: long = format_coor(coors[0]) + "N "
    else: long = format_coor(abs(coors[0])) + "S "

    if coors[1] > 0: lat = format_coor(coors[1]) + "E"
    else: lat = format_coor(abs(coors[1])) + "W"

    return long + lat

def format_coor(coor):
    """
    Formats one coordinate value from a decimal format to
    a sexagesimal format.
    :param coor: float coordinate value
    :return str: sexagesimal coordinate string
    """
    minutes, degrees = modf(coor)
    seconds, minutes = modf(minutes*60)
    seconds = str(round(seconds*60, 1))
    if seconds[0] == "0":
        seconds = "0"+seconds

    return str(int(degrees))+"°"+str(int(minutes))+"\'"+seconds+"\""