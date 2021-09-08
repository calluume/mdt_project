import sys, os.path, json, pickle
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.offline as opy
import plotly.graph_objs as go

from mdt_webapp.mdt.FoliumMap import FoliumMap
from mdt_webapp.mdt.Network import Network, Segment, Node
from mdt_webapp.mdt.NetworkCreator import Creator
from mdt_webapp.mdt.Emissions import calculate_net_emissions, calculate_seg_emissions

from mdt_project.settings import OBJ_DIR, CSV_DIR

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

CartoDB_PositronNoLabels = 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png'
CartoDB_VoyagerNoLabels = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png'
times = ['6:00', '7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
seg_limit = None

emissionsID = 'em'
speedID = 'sp'
flowID = 'fl'

emissions_colour = '#6cb165'
speed_colour = '#db4d41'
flow_colour = '#4c66ba'

@login_required()
def create_objs(request):
    """
    Creates the network creator page. If a form has been submitted,
    the specified networks are created.
    """
    if request.POST.get('osm', None) == 'True': osm=["query", "mancunian", "oldham", "ancoats", "a57"]
    else: osm=None

    if request.POST.get('tt', None) == 'True': tt='TOMTOM_flow_time2019.json'
    else: tt=None

    if request.POST.get('mdt', None) == 'True': mdt=True
    else: mdt=False

    creator = Creator()
    osm, tt, mdt = creator.create_networks(osm, tt, mdt, verbose=True)

    # The state is printed beneath the network creator form, showing
    # whether or not networks have been built.
    if osm==None and tt==None or mdt==False: context = {'state': 'Select networks to create'}
    else: context = {'state': 'Network(s) created'}

    return render(request, 'mdt_webapp/create.php', context)

def show_emissions(request):
    """
    Displays the emissions map and data.
    """
    
    network = pickle.load( open( OBJ_DIR+"mdt_network.p", "rb" ) )
    fol = FoliumMap(style=CartoDB_PositronNoLabels)

    # Emissions are calculated with any modifications. The average factors
    # can then be calculated, along with finding the worst emitting and most
    # congested segment.
    modifiers = handle_network_modifiers(request)
    calculate_net_emissions(network, type_modifiers=modifiers[:5], engine_petrol_prop=modifiers[5]/100, temperature=modifiers[6])
    congested, emitter, max_val = network.calculate_factors(get_highest_emissions=True)

    fol.draw_network(network, metric='emissions', lower_bounds=max_val*(modifiers[8]/100), upper_bounds=max_val*(modifiers[9]/100), draw_zero_values=modifiers[7], seg_limit=seg_limit)
    fol.add_time_layers()

    context = {'my_map': fol,
               'network': network,
               'metric': 'Emissions',
               # Graphs are generated during the request stage to show to the user.
               'graphs': [[[emissionsID, 'Average Hourly Segment Emissions'], make_barchart(network.get_av_emissions(), 'Total CO<sub>2</sub> Emissions per Hour (g)', emissions_colour)],
                          [[flowID, 'Average Segment Traffic Flow Rate'], make_barchart(network.get_av_vph(),'No. of Vehicles per Hour',flow_colour)]],
               # Data is formatted so that it can be easily displayed by Django.
               'data': format_data(network),
               'worst': zip(['Most Congested', 'Largest Emitter'], [congested, emitter]),
               'editor': True,
               # The modifiers are also returned to the template so the network modifier
               # displays the previously given values.
               'type_props': zip(['two', 'cars', 'buses', 'lgvs', 'hgvs'], ['Mopeds/Motorcycles', 'Passenger Cars/Taxis', 'Buses/coaches', 'LGVs', 'HGVs'], modifiers[:5]),
               'modifiers': modifiers[5:]}

    return render(request, 'mdt_webapp/map.php', context)

def show_flow(request):  
    """
    Displays flow map and data.
    """
    network = pickle.load( open( OBJ_DIR+"mdt_network.p", "rb" ) )
    fol = FoliumMap()
    
    # Emissions still have to be calculated here as the data is still displayed on the
    # flow map page and in the inspector panel.
    modifiers = handle_network_modifiers(request)
    calculate_net_emissions(network, type_modifiers=modifiers[:5], engine_petrol_prop=modifiers[5]/100, temperature=modifiers[6])
    congested, emitter, max_val = network.calculate_factors(get_highest_speed=True)

    fol.draw_network(network, metric='flow', lower_bounds=max_val*(modifiers[8]/100), upper_bounds=max_val*(modifiers[9]/100), draw_zero_values=modifiers[7], seg_limit=seg_limit)
    fol.add_time_layers()
    
    context = {'my_map': fol,
               'network': network,
               'metric': 'Flow',
               # Graphs are generated for the page creation, but are returned in a different
               # order that prioritises the flow data.
               'graphs': [[[speedID, 'Average Vehicle Speed'], make_barchart([val * 0.62137119223733 for val in network.get_av_speed()], 'Speed (mph)', speed_colour)],
                          [[flowID, 'Average Segment Traffic Flow Rate'], make_barchart(network.get_av_vph(),'No. of Vehicles per Hour',flow_colour)]],
               'data': format_data(network, False),
               'worst': zip(['Most Congested', 'Largest Emitter'], [congested, emitter]),
               'editor': True,
               'type_props': zip(['two', 'cars', 'buses', 'lgvs', 'hgvs'], ['Mopeds/Motorcycles', 'Passenger Cars/Taxis', 'Buses/coaches', 'LGVs', 'HGVs'], modifiers[:5]),
               'modifiers': modifiers[5:]}

    return render(request, 'mdt_webapp/map.php', context)

def create_inspector(request, segID, modifiers):
    """
    Creates an inspector panel.
    :param segID:     ID for segment being inspected
    :param modifiers: string containing network modifiers
    """
    network = pickle.load( open( OBJ_DIR+"mdt_network.p", "rb" ) )
    modifiers = format_modifier_string(modifiers)
    segment = network.get_network_segments()[segID]

    # Emissions are calculated according to the network modifiers.
    calculate_seg_emissions(segment, segment.get_attributes()['vehicleProps'], engine_type_distribution=[modifiers[5]/100, 1-(modifiers[5]/100)], type_modifiers=modifiers[:5], temperature=modifiers[6])

    return render(request, 'mdt_webapp/inspector.php', {'network': network, 'segID': segID, 'type_props': modifiers[:5]})

def create_landing(request):
    """
    Returns the landing page template.
    """
    context = {}
    return render(request, 'mdt_webapp/index.php', context)

def login_error(request):
    """
    Returns an error page for unauthorised access to
    the network creator page.
    """
    context = {}
    return render(request, 'mdt_webapp/login_error.php', context)

def download_network(request, zip_output, modifiers):
    """
    Creates a zip file for the current network, and returns
    the file as a response.
    """
    network = pickle.load( open( OBJ_DIR+"mdt_network.p", "rb" ) )
    modifiers = format_modifier_string(modifiers)
    calculate_net_emissions(network, type_modifiers=modifiers[:5], engine_petrol_prop=modifiers[5]/100, temperature=modifiers[6])

    zip_file = network.export_network(zip_output=zip_output)

    with open(zip_file, 'rb') as network: 
        response = HttpResponse(network.read()) 
        response['content_type'] = 'application/zip' 
        response['Content-Disposition'] = 'attachment;filename='+zip_output
        return response

def make_barchart(y, y_label, colour):
    """
    Generates a barchart for the given data.
    :param y:       y values
    :param y_label: y axis label
    :param colour:  bar colour
    :return div:    Plotly graph
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(x=times,
                         y=y,
                         marker_color=colour))
    fig.update_layout(
        plot_bgcolor='rgb(244,244,244)',
        barmode='group',
        yaxis_title=y_label,
        xaxis_title='Hour',
        margin=dict(r=40, l=60, t=40, b=50),
        height=300,
        hovermode="x unified",
        hoverlabel=dict(bordercolor='white', bgcolor='rgb(244,244,244)', font=dict(color='#9c9c9c'))
    )

    # The graph is returned in a div format.
    div = opy.plot(fig, auto_open=False, output_type='div')
    return div

def format_data(network, emissions_first=True):
    """
    Formats the network data in arrays that Django
    can easily process in the page template.
    :param emissions_first: whether emissions are prioritised
    :return data:           data array for Django to print
    """
    em_hds = ["em", "Emissions Data", "Time", "CO<sub>2</sub> Emissions per Hour (g)", "Percent Deviation (%)"]
    sp_hds = ["sp", "Speed Data", "Time", "Average Speed (mph)", "Percent Deviation (%)"]
    fl_hds = ["fl", "Flow Rate Data", "Time", "Average Flow Rate", "Percent Deviation (%)"]

    em_vals = network.get_av_emissions()
    sp_vals = [round(val * 0.62137119223733, 2) for val in network.get_av_speed()]
    fl_vals = network.get_av_vph()

    # The first table is the averages for emissions, speed and flow rate.
    em_av = sum(em_vals)/len(em_vals)
    sp_av = sum(sp_vals)/len(sp_vals)
    fl_av = sum(fl_vals)/len(fl_vals)

    em_abo = []
    sp_abo = []
    fl_abo = []

    # The hourly percent deviation for each measure is calculated.
    for i in range(len(em_vals)):
        em_abo.append(round((em_vals[i] - em_av)*100/em_av, 2))
        sp_abo.append(round((sp_vals[i] - sp_av)*100/sp_av, 2))
        fl_abo.append(round((fl_vals[i] - fl_av)*100/fl_av, 2))

    av_hds = ["av", "Daily Average", "Metric", "Average"]
    avs = zip(["Emissions", "Speed", "Traffic Flow Rate"],
              [round(em_av, 2), round(sp_av, 2), round(fl_av, 2)]) 
    
    data = [[av_hds, avs]]

    # Either emissions or flow can be prioritised, changing
    # the order they are shown in.
    if emissions_first:
        data.append([em_hds, zip(times, em_vals, em_abo)])
        data.append([fl_hds, zip(times, fl_vals, fl_abo)])
        data.append([sp_hds, zip(times, sp_vals, sp_abo)])
    else:
        data.append([fl_hds, zip(times, fl_vals, fl_abo)])
        data.append([sp_hds, zip(times, sp_vals, sp_abo)])
        data.append([em_hds, zip(times, em_vals, em_abo)])

    return data

def handle_network_modifiers(request):
    """
    Formats any modifiers in the current request.
    :return modifiers: network modifiers
    """
    if request.method == "POST":
        # If there are POST variables, there has changed the network,
        # so modifiers are formatted.
        params = ['two', 'cars', 'buses', 'lgvs', 'hgvs', 'petrol', 'temp', 'draw', 'lower', 'upper']
        modifiers = []
        for param in params:
            if param != 'draw':
                modifiers.append(float(request.POST.get(param, None)))
            else:
                if request.POST.get('draw', None) == 'True':
                    modifiers.append(True)
                else: modifiers.append(False)
        
        if modifiers[8] > modifiers[9]: modifiers[8], modifiers[9] = modifiers[9], modifiers[8]

        return modifiers

    else:
        # If the method is not POST, the user has not changed the network,
        # so default modifier values are provided.
        return [1, 1, 1, 1, 1, 65.1, 10, True, 0, 100]

def format_modifier_string(modifiers):
    """
    Formats the modifier string fetched from the URL
    into a python array.
    :param modifiers:     URL modifier string
    :return new_modifers: modifier array
    """
    new_modifiers = []
    modifiers = modifiers.split(',')
    for i in range(len(modifiers)):
        if i != 7:
            new_modifiers.append(float(modifiers[i]))
        elif modifiers[i] == 'True': new_modifiers.append(True)
        else: new_modifiers.append(False)
    return new_modifiers