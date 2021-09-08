<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Manchester Digital Twin</title>
    {% load static %}
    {% load mdt_tags %}
    <link rel="preconnect" href="https://fonts.gstatic.com">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100;300;400;500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="{% static 'mdt_webapp/main-style.css' %}">
    <script src="{% static 'mdt_webapp/js/js.js' %}"></script>
</head>
<body>

{% if segID %}
    {% if network %}
    <div id="inspector" style="height: 100%; width: 100%;">
        
        {% get_attributes segID as attributes %}
        {% if attributes %}
        {% get_name segID as streetName %}
        {% get_seg_data segID as seg_data %}
        <h2 class='sidebar-title'>Inspecting: <i>{{streetName}}</i></h2>
        <div id="test"></div>
        <button onclick="inspect(0)" class='inspector-hide'><img src="{% static 'mdt_webapp/images/close.svg' %}"></button>
        <div class='sidebar-panel-hd'>
            {{streetName}} Map
            <button class='sidebar-panel-hide' onclick="togglePanel('map-table')">
                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" style="display: none;" id="map-table-show">
                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" id="map-table-hide">
            </button>
        </div>
        <div class='sidebar-panel-dat minimap-panel visible' id="map-table">
            {% get_minimap segID as minimap %}
            {{ minimap|safe }}
        </div>
        <div class='sidebar-panel-hd'>
            Characteristics
            <button class='sidebar-panel-hide' onclick="togglePanel('char-table')">
                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" style="display: none;" id="char-table-show">
                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" id="char-table-hide">
            </button>
        </div>

        <div class='sidebar-panel-dat visible' id="char-table">
            <table class='sidebar-data-table'>
                <tbody>

                    {% for header, value in attributes %}
                    <tr class='sidebar-data-row'>
                        <td class='sidebar-data-val'><b><i>{{ header }}</i></b></td>
                        <td class='sidebar-data-val'>{{ value }}</td>
                    </tr>
                    {% endfor %}

                </tbody>
            </table>
        </div>
        {% get_seg_graph segID 'Flow' as flow_graph %}
        {% if flow_graph %}
        <div class='sidebar-panel-hd'>
            Flow
            <button class='sidebar-panel-hide' onclick="togglePanel('rd-fl-graph')">
                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" style="display: none;" id="rd-fl-graph-show">
                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" id="rd-fl-graph-hide">
            </button>
        </div>
        <div class='sidebar-panel-dat visible' id="rd-fl-graph">
            {{ flow_graph|safe }}
        </div>
        {% endif %}
        {% get_seg_graph segID 'Emissions' as emis_graph %}
        {% if emis_graph %}
        <div class='sidebar-panel-hd'>
            Emissions
            <button class='sidebar-panel-hide' onclick="togglePanel('rd-em-graph')">
                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" style="display: none;" id="rd-em-graph-show">
                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" id="rd-em-graph-hide">
            </button>
        </div>
        <div class='sidebar-panel-dat visible' id="rd-em-graph">
            {{ emis_graph|safe }}
        </div>
        {% endif %}
        {% get_vehicle_pie segID as piechart %}
        {% if piechart %}
        <div class='sidebar-panel-hd'>
            Vehicle Distribution
            <button class='sidebar-panel-hide' onclick="togglePanel('rd-pie-graph')">
                <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" style="display: none;" id="rd-pie-graph-show">
                <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" id="rd-pie-graph-hide">
            </button>
        </div>
        <div class='sidebar-panel-dat visible' id="rd-pie-graph">
            {{ piechart|safe }}
        </div>
        {% endif %}
        {% get_seg_data segID as seg_data %}
        {% if seg_data %}
        {% autoescape off %}
            {% for metric in seg_data %}
            <div class='sidebar-panel-hd'>
                {{ metric.0.1 }}
                <button class='sidebar-panel-hide' onclick="togglePanel('{{ metric.0.0 }}-table')">
                    <img src="{% static 'mdt_webapp/images/down.svg' %}" class="show-hide-btn" id="{{ metric.0.0 }}-table-show">
                    <img src="{% static 'mdt_webapp/images/up.svg' %}" class="show-hide-btn" style="display: none;" id="{{ metric.0.0 }}-table-hide">
                </button>
            </div>
            <div class='sidebar-panel-dat hidden' id="{{ metric.0.0 }}-table">
                <table class='sidebar-data-table'>
                    <tbody>
                        <tr>
                            {% for header in metric.0|slice:"2:" %}
                            <th class='sidebar-data-header'>{{ header }}</th>
                            {% endfor %}
                        </tr>
                        {% for row in metric.1 %}
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
        {% endautoescape %}
        {% endif %}
        {% endif %}
        </div>
    {% endif %}
{% endif %}

</body>
</html>