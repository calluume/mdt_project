<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Manchester Digital Twin | {{ metric }} Map</title>
    {{my_map.header.render|safe}}
    {% load static %}
    {% load mdt_tags %}

    <link rel="preconnect" href="https://fonts.gstatic.com">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100;300;400;500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="{% static 'mdt_webapp/main-style.css' %}">
    <script src="{% static 'mdt_webapp/js/js.js' %}"></script>
    <link rel="icon" type="image/png" href="{% static 'mdt_webapp/images/fav.png' %}">
    <script src="http://code.jquery.com/jquery-3.5.1.js"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style> html { overflow: hidden; } </style>
</head>


<body>
    <div class='ls' id='ls-stay'>
        <div class='ls-txt'>
            <h2>Drawing Network Map</h2>
        </div>
        <div class="progress-bar">
            <span class="bar">
                <span class="progress"></span>
            </span>
        </div>   
    </div>
    <div class='ls' id='ls-go' style="display: none;">
        <div class='ls-txt'>
            <h2 id='ls-msg'>Loading Network Map<br>(this may take some time)</h2>
        </div>
        <div class="progress-bar">
            <span class="bar">
                <span class="progress"></span>
            </span>
        </div> 
    </div>
    <div class='nav-div'>
        <table class='nav-table'>
            <tbody>
                <tr>
                    <td>
                        <a href="http://localhost:8000" class='nav-link'>
                            <img src="{% static 'mdt_webapp/images/white-logo.svg' %}" id='logo-img'>
                        </a>
                    </td>
                    <td class='nav-td hide-700'>
                        <a href="http://localhost:8000" class='nav-link'>Home</a>
                    </td>
                    <td class='nav-td hide-700'>
                        <button onclick="redirectTo('flow', 'Loading Flow Map')" class='nav-link nav-btn'>Traffic Flow</button>
                    </td>
                    <td class='nav-td hide-700'>
                        <button onclick="redirectTo('emissions', 'Loading Emissions Map')" class='nav-link nav-btn'>Emissions</button>
                    </td>
                    <td class='nav-td hide-700'>
                        <button onclick='toggleAbout()' class='nav-link nav-btn'>Instructions</button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    <table class='map-table'>
        <tbody>
            <tr>
                <td class='map-panel'>
                    <div class='map-div'>
                    {% get_map as map%}
                        {% if map %}
                            {{ map|safe }}
                        {% else %}
                            ive done a shit
                        {% endif %}
                        <button class='sidebar-toggle hide-700' onclick="showSidebar()" id="sidebar-btn-show"><img src="{% static 'mdt_webapp/images/left-black.svg' %}"></button>
                    </div>
                </td>
                <td class='map-sidebar hide-700' id='sidebar'>
                    <button class='sidebar-toggle' onclick="showSidebar()" id="sidebar-btn-hide"><img src="{% static 'mdt_webapp/images/right-black.svg' %}"></button>
                    {% autoescape off %}
                    <div class='sidebar-div'>

                        <!-- Network Averages -->

                        <h2 class='sidebar-title'>Network {{ metric }} Map</h2>

                        <!-- Debug panel -->
                        {% if editor is True %}
                            <div class='sidebar-panel-hd'>
                                Segment Editor
                                <button class='sidebar-panel-hide' onclick="togglePanel('edit-table')">
                                    <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" style="display: none;" id="edit-table-show">
                                    <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" id="edit-table-hide">
                                </button>
                            </div>
                            <div class='sidebar-panel-dat visible' id="edit-table">
                                <form id="edit-form" method="POST">
                                    {% csrf_token %}
                                    <table class="edit-form-table">
                                        <tbody>
                                            <tr>
                                                <th class='sidebar-data-header' style="padding: 5px;" colspan="3">Vehicle Type Multipliers</th>
                                            </tr>
                                            {% if type_props %}
                                            {% for id, type, prop in type_props %}
                                            <tr>
                                                <td class="edit-form-label edit-form-td">{{ type }}</td>
                                                <td class="edit-form-slider edit-form-td">
                                                    <input name="{{ id }}" id="{{ id }}-slider" class="slider" type="range" min="0" max="10" value="{{ prop }}" step="0.1"></td>
                                                <td class="edit-form-val edit-form-td"><p id="{{ id }}-val">1.0</p></td>
                                            </tr>
                                            {% endfor %}
                                            {% endif %}
                                        </tbody>
                                    </table>
                                    <table class="edit-form-table">
                                        <tbody>
                                            <tr>
                                                <th class='sidebar-data-header' style="padding-bottom: 5px;" colspan="3">Engine Type Distribution</th>
                                            </tr>
                                            <tr>
                                                <td style="width: 15%; text-align: center;">Petrol</td>
                                                <td style="width: 70%; text-align: center;">
                                                    <input name="petrol" id="engine-slider" class="slider" type="range" min="0" max="100" value="{{ modifiers.0 }}" step="0.1"></td>
                                                <td style="width: 15%; text-align: center;">Diesel</td>
                                            </tr>
                                            <tr>
                                                <td style="width: 15%; text-align: center;" id='petrol-val'>{{ modifiers.0 }}%</td>
                                                <td style="width: 70%; text-align: center;"></td>
                                                <td style="width: 15%; text-align: center;" id='diesel-val'>{% diesel_prop modifiers.0 %}%</td>
                                            </tr>
                                        </tbody>  
                                    </table>
                                    <table class="edit-form-table">
                                        <tbody>
                                            <tr>
                                                <th class='sidebar-data-header' style="padding-bottom: 5px;" colspan="4">Other Options</th>
                                            </tr>
                                            <tr>
                                                <td style="width: 30%; text-align: center;">Value Lower Boundary (%)</td>
                                                <td style="width: 20%; text-align: center;">
                                                    <input type="number" id="lower" name="lower" min="0" max="100" value="{{ modifiers.3 }}">
                                                <td style="width: 30%; text-align: center;">Value Upper Boundary (%)</td>
                                                <td style="width: 20%; text-align: center;">
                                                    <input type="number" id="upper" name="upper" min="0" max="100" value="{{ modifiers.4 }}">
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="width: 30%; text-align: center;">Temperature (°C)</td>
                                                <td style="width: 20%; text-align: center;">
                                                    <input type="number" id="temperature" name="temp" min="-40" max="40" value="{{ modifiers.1 }}">
                                                <td style="width: 30%; text-align: center;">Draw Zero Values</td>
                                                <td style="width: 20%; text-align: center;"><input type="checkbox" id="draw" name="draw" checked="{{ modifiers.2 }}" value="{{ modifiers.2 }}"></td>
                                            </tr>
                                        </tbody>  
                                    </table>
                                </form>
                                <table style="width: 100%; margin-bottom: 5px;">
                                    <tbody>
                                        <tr>
                                            <td class="form-btn" style="width: 50%; text-align: center;"><button onclick="submitEditForm()">Make Changes</td>
                                            <td class="form-btn" style="width: 50%; text-align: center;"><button onclick="resetEditor()">Reset Values</td>
                                        </tr>
                                    </tbody>  
                                </table>
                            </div>
                        {% endif %}

                        <!-- Map Legend Panel -->
                        <div class='sidebar-panel-hd'>
                            Map Legend
                            <button class='sidebar-panel-hide' onclick="togglePanel('legend-graph')">
                                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" style="display: none;" id="legend-graph-show">
                                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" id="legend-graph-hide">
                            </button>
                        </div>
                        <div class='sidebar-panel-dat visible' id="legend-graph" style="background-color: white;">
                            {% if metric == 'Emissions' %}
                                <img src="{% static 'mdt_webapp/images/emissions-legend.png' %}" style="width: 100%;">
                            {% else %}
                                <img src="{% static 'mdt_webapp/images/flow-legend.png' %}" style="width: 100%;">
                            {% endif %}
                        </div>

                        <!-- Graph panels -->
                        {% if graphs %}
                        {% for graph in graphs %}
                        <div class='sidebar-panel-hd'>
                            {{ graph.0.1 }}
                            <button class='sidebar-panel-hide' onclick="togglePanel('{{ graph.0.0 }}-graph')">
                                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" style="display: none;" id="{{ graph.0.0 }}-graph-show">
                                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" id="{{ graph.0.0 }}-graph-hide">
                            </button>
                        </div>
                        <div class='sidebar-panel-dat visible' id="{{ graph.0.0 }}-graph">
                            {{ graph.1|safe }}
                        </div>
                        {% endfor %}
                        {% endif %}
                        {% if worst %}
                        <div class='sidebar-panel-hd'>
                            Show Worst Segments
                            <button class='sidebar-panel-hide' onclick="togglePanel('wst-table')">
                                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" id="wst-table-show">
                                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" style="display: none;" id="wst-table-hide">
                            </button>
                        </div>
                        <div class='sidebar-panel-dat hidden' id="wst-table">
                            <table class='sidebar-data-table' style="border: none;">
                                <tbody>
                                    <tr>
                                        {% for label, key in worst %}
                                            <td style="width: 50%; text-align: center; padding: 5px 0;">
                                                <button onclick="inspect({{ key }})">{{ label }}</button>
                                            </td>
                                        {% endfor %}
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        {% endif %}
                        <!-- Table panels -->
                        {% if data %}
                        {% for dataset in data %}
                        <div class='sidebar-panel-hd'>
                            {{ dataset.0.1 }}
                            <button class='sidebar-panel-hide' onclick="togglePanel('{{ dataset.0.0 }}-table')">
                                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" id="{{ dataset.0.0 }}-table-show">
                                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" style="display: none;" id="{{ dataset.0.0 }}-table-hide">
                            </button>
                        </div>
                        <div class='sidebar-panel-dat hidden' id="{{ dataset.0.0 }}-table">
                            <table class='sidebar-data-table'>
                                <tbody>
                                    <tr>
                                        {% for header in dataset.0|slice:"2:" %}
                                        <th class='sidebar-data-header'>{{ header }}</th>
                                        {% endfor %}
                                    </tr>
                                    {% for row in dataset.1 %}
                                    <tr class='sidebar-data-row'>
                                        {% for column in row %}
                                        <td class='sidebar-data-val'>{{ column }}</td>
                                        {% endfor %}
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        {% endfor %}
                        {% endif %}
                        <div class='sidebar-panel-hd'>
                            Export Network
                            <button class='sidebar-panel-hide' onclick="togglePanel('dwn-table')">
                                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" id="dwn-table-show">
                                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" style="display: none;" id="dwn-table-hide">
                            </button>
                        </div>
                        <div class='sidebar-panel-dat hidden' id="dwn-table">
                            <table class='sidebar-data-table' style="border: none;">
                                <tbody>
                                    <tr>
                                        <td style="width: 100%; text-align: center; padding: 5px 0;"><button onclick="downloadNetwork('network.zip')">Download as a 'zip' file</button></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
    <div class='sidebar-div inspector-div hide-700' id='inspector' style="display: none;">
        <img src="{% static 'mdt_webapp/images/spin-nogradient.png' %}" class='ls-spin'>
    </div>
    {% endautoescape %}

    <div id='shadow-screen' style="display: none;">
        <div id='about-div' class='about'>
            <div id='about-content-div'>
                <button class='about-btn' onclick="toggleAbout()"><img src="{% static 'mdt_webapp/images/close.svg' %}"></button>
                <img class='about-logo' src="{% static 'mdt_webapp/images/colour-logo.svg' %}">
                <h2>How to use the MDT</h2>
                <p>
                    Once a metric has been chosen from the navigation bar, the map should displayed on the screen. The map
                    controls are located in the top right of the screen:</p>
                    <ul>
                        <li>To zoom in or out, click the <img src="{% static 'mdt_webapp/images/plus.png' %}" style="height: 0.8em; margin: 0 5px;"> or <img src="{% static 'mdt_webapp/images/minus.png' %}" style="height: 0.8em; margin: 0 5px;"> symbols.</li>
                        <li>To change the current time, hover over <img src="{% static 'mdt_webapp/images/layers.png' %}" style="height: 1em; margin: 0 5px;">
                            and select a new time segment.</li>
                    </ul>
                <p>
                    The sidebar to the right of the screen shows the map data in more depth. This includes the hourly averages
                    for <i>CO<sub>2</sub> emissions</i>, <i>vehicle speed</i> and the <i>traffic flow rate</i>, which is the
                    number of vehicles that pass a given point on a road. The real values of each measurement can also be found below the
                    graphs in the data section. At the bottom of the sidebar panel, the '<i>Show Worst Segments</i> ' will
                    display the road segment with the highest average hourly emissions, and the worst 'speed performance index,'
                    which is the ratio of the average speed to the maximum possible speed (the speed limit).
                    <br><br>
                    Hovering over a part of the network will display its name, and clickling on the inspect button should display
                    its details.
                </p>
                <h3>Changing the network</h3>
                <p>
                    Changes can also be made to the network emissions through the '<i>Network Editor</i> ' section at the top
                    of the sidebar panel:</p>
                    <ul>
                        <li>
                            The vehicle type multipliers change the proportion of each of the 5 vehicle types included in the MDT.
                            Each road segment has their own recorded distribution, but these modifiers change this distribution
                            in proportion to their real world values.
                        </li>
                        <li>The engine type distribution changes the proportion of petrol and diesel vehicles on the network.</li>
                        <li>Temperature changes the temperature used during the emissions calculations.</li>
                        <li>
                            Changing the upper and lower boundary values limits the segments that are drawn on the final map, and
                            can be done for network analysis or to improve performance. These values are used to calculate the bounds
                            as a percent of the highest average value throughout the network.
                        </li>
                        <li>
                            Changing the upper and lower boundary values limits the segments that are drawn on the final map, and
                            can be done for network analysis or to improve performance. These values are used to calculate the bounds
                            as a percent of the highest average value throughout the network.
                        </li>
                        <li>
                            Unchecking 'draw zero values' means that segments with no recorded vehicles throughout the day are not
                            drawn on the final map. This can also be done to improve performance.
                        </li>
                    </ul>
                <h3>Inspecting road segments</h3>
                <p>
                    The inspector panel can be displayed by clicking one of the map's road segments, and then clicking inspect.
                    First, this will show the physical characteristics of the street such as length or number of lanes, and will
                    then display the flow and emissions values for the specified street. The vehicle distribution, including any
                    modifications, and real values will also be shown.
                </p>
                    <img src="{% static 'mdt_webapp/images/about-example.png' %}" style="width: 50%;margin: 10px 25% 0;box-shadow: 0px 0px 4px 0px rgb(0 0 0 / 50%);">

                <h3>Final Notes</h3>

                <p>
                    This was developed by Callum Evans as part of a 3<sup>rd</sup> year project at the University of Exeter, if you
                    have any feedback to be included in the project report, please fill out the form <a href="https://forms.gle/x2fk4ipp828Qy4SDA">here</a>.
                    <br><br>Also, if you do encounter any major issues whilst using the system, please contact ce347@exeter.ac.uk.<br><br>
                    Icons made by <a href="https://www.flaticon.com/authors/chanut" title="Chanut">Chanut</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a><br>
                    Logo by <a href="https://www.vecteezy.com/free-vector/sports">Vecteezy</a>
                    <br><br><a href="http://localhost:8000/create/" style="font-size: small;">admin page</a></p>
            </div>    
        </div>
    </div>
    {% if map %}
        <script>
            ls = document.getElementById('ls-stay')
            ls.classList.add('fadeOut')
            setTimeout(function(){ls.style.display = 'none'}, 500)
        </script>
    {% endif %}
</body>
</html>