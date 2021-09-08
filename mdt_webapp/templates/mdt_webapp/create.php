<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Manchester Digital Twin | Network Creator</title>
        {{my_map.header.render|safe}}
        {% load static %}
        <link rel="preconnect" href="https://fonts.gstatic.com">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100;300;400;500;700;900&display=swap" rel="stylesheet">
        <link rel="stylesheet" type="text/css" href="{% static 'mdt_webapp/main-style.css' %}">
        <link rel="icon" type="image/png" href="{% static 'mdt_webapp/images/fav.png' %}">
        <script src="{% static 'mdt_webapp/js/js.js' %}"></script>
    </head>
    <body>
        <div class='ls' id='ls-go' style="display: none;">
            <div class='ls-txt'>
                <h2>Drawing Network Map</h2>
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
                            <img src="{% static 'mdt_webapp/images/white-logo.svg' %}" id='logo-img'>
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
                    </tr>
                </tbody>
            </table>
        </div>
        <div class="creator-container">
            <div class='creator-div'>
                <form id='creator-form' method="POST" onsubmit="setState()">
                    {% csrf_token %}
                    <input type="checkbox" id="osm" name="osm" value="True">
                    <label for="vehicle1"> OSM</label><br>
                    <input type="checkbox" id="tt" name="tt" value="True">
                    <label for="vehicle2"> TOMTOM</label><br>
                    <input type="checkbox" id="mdt" name="mdt" value="True">
                    <label for="vehicle3"> MDT</label><br>
                    <input type="hidden" name="username" value="{{ username }}">
                    <input type="hidden" name="password" value="{{ password }}">
                </form>
                <button onclick="submitCreatorForm()">Create</button>
                {% if state %}
                    <h2 id="state-msg">{{ state }}</h2>
                {% endif %}
            </div>
        </div>
    </body>
    <script>
        function submitCreatorForm() {
            document.getElementById('state-msg').innerHTML = 'Creating Networks (check console)...';
            document.getElementById('creator-form').submit();
        }
    </script>
</html>