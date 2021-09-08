<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Manchester Digital Twin</title>
    {% load static %}
    {% load mdt_tags %}
    <link rel="preconnect" href="https://fonts.gstatic.com">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100;300;400;500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="{% static 'mdt_webapp/main-style.css' %}">
    <link rel="stylesheet" type="text/css" href="{% static 'mdt_webapp/landing-style.css' %}">
    <script src="{% static 'mdt_webapp/js/landing-js.js' %}"></script>
    <link rel="icon" type="image/png" href="{% static 'mdt_webapp/images/fav.png' %}">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
</head>
<body>


    <div class='ls' id='ls-go' style="display: none;">
        <div class='ls-txt'>
            <h2>Loading Network Map<br>(this may take some time)</h2>
        </div>
        <div class="progress-bar">
            <span class="bar">
                <span class="progress"></span>
            </span>
        </div> 
    </div>
    <div class="homescreen-div">
        <img src="{% static 'mdt_webapp/images/colour-logo.svg' %}" width="100px">
        <h2 class="homescreen-title">Manchester Digital Twin</h2>
        <p>An environmental evaluation tool for urban design.</p>
        <button class="homescreen-btn" onclick="redirectTo('flow')">Flow Map</button>
        <button class="homescreen-btn" onclick="redirectTo('emissions')">Emissions Map</button>
        <img id="homescreen-scroll" src="{% static 'mdt_webapp/images/scroll-down.svg' %}">
    </div>
    <div class="main-content-div">
        <h2 class="main-content-hdr">About the project</h2>
        <p class="main-content-p">
            The human population is expected to become increasingly more urban in the coming decades, with
            the United Nations predicting that 68% of people will live in cities by 2030. Alongside this,
            cities also currently consume around two-thirds of the world's energy and produce 70% of its
            emissions, so this means ensuring our future urban growth is sustainable will be crucial in
            fighting climate change.
            <br><br>
            One way that cities can produce more emissions is through their busy or congested roads,
            with a report by the EU finding that the transportation sector accounted for 27% of the EU's greenhouse
            gas emissions in 2017. A majority of this comes from road transportation, and although there are indirect
            factors such as the production of vehicles and fuel, the 'slower stop-and-start' conditions seen on congested
            roads can have a large impact on emissions.
            <br><br>
            So considering this, the goal of the Manchester Digital Twin project is to create a tool that can help
            developers, urban planners and non-experts understand how congestion and the layout of a city affects
            its greenhouse gas emissions. This is done through modelling traffic to display how conditions such as
            congestion or vehicle types affect the network's overall emissions. The MDT also aims to demonstrate basic
            digital twin technology and show their promise within the field of urban science.
            <br><br>
            To get started, click on the flow or emissions maps above, and read the 'About the MDT' to find out
            how to use the system. Feedback is also greatly appreciated and can be given <a href="https://forms.gle/x2fk4ipp828Qy4SDA">here</a>
        </p>
        <!--<table style="width: 100%; margin: 40px 0;"><tbody><tr>
            <td style="text-align: right; padding-right: 20px;">
                <button class="main-btn" onclick="redirectTo('flow')">View Flow Map</button></td>
            <td style="text-align: left; padding-left: 20px;">
                <button class="main-btn" onclick="redirectTo('emissions')">View Emissions Map</button></td>
        </tr></tbody></table>-->
        <table class="content-table">
            <tbody>
                <tr class="content-table-row">
                    <td class="content-table-data">
                        <h2>What are Digital Twins?</h2>
                        <p>
                            Digital twins are virtual representations of real-world systems and can
                            be applied to an incredibly wide variety of applications, including in
                            manufacturing, healthcare and urban planning. They allow designers to
                            be able to predict issues and gain a deeper understanding of how complex
                            systems operate.<br><br>
                            Digital twin technology has become more popular in urban science in recent
                            years due to the increasing amount of data surrounding our cities. Digital
                            twins have already been deployed in cities like Singapore, Helsinki and
                            Los Angeles, but the number of active systems is predicted to grow to 500
                            by 2025.
                        </p>
                    </td>
                    <td class="content-table-data content-table-img hide-700" style="background-image: url('{% static 'mdt_webapp/images/dt.jpg' %}')"></td>
                </tr>
                <tr class="content-table-row content-img-responsive show-700"><td class="content-table-data content-table-img" style="background-image: url('{% static 'mdt_webapp/images/dt.jpg' %}')"></td></tr>
            </tbody>
        </table>
        <table class="content-table">
            <tbody>
                <tr class="content-table-row">
                <td class="content-table-data content-table-img hide-700" style="background-image: url('{% static 'mdt_webapp/images/manc.jpg' %}')"></td>
                    <td class="content-table-data">
                        <h2>Why Manchester?</h2>
                        <p>
                            Manchester is currently seeing a huge increase in interest and investment,
                            which made the city the fastest growing tech hub in Europe between 2018 and 2019.
                            This has caused a huge amount of development throughout Manchester that has
                            not slowed down, even despite the COVID-19 pandemic, meaning that Manchester is
                            incredibly relevant for a project such as this.
                            <br><br>
                            Along with this, the datasets used in digital twins are very important to
                            their accuracy, and there is a wide variety of good, useful data available
                            for Manchester.
                        </p>
                    </td>
                </tr>
                <tr class="content-table-row content-img-responsive show-700"><td class="content-table-data content-table-img" style="background-image: url('{% static 'mdt_webapp/images/manc.jpg' %}')"></td></tr>
            </tbody>
        </table>
        <table class="content-table">
            <tbody>
                <tr class="content-table-row">
                    <td class="content-table-data">
                        <h2>How does the model work?</h2>
                        <p>
                            The MDT network is based on the open-source OpenStreetMap dataset and flow data 
                            is from the TOMTOM traffic index. Emissions are calculated using an implementation
                            of COPERT, the European Union's industrial standard for emissions modelling.
                        </p>
                    </td>
                    <td class="content-table-data content-table-img hide-700" style="background-image: url('{% static 'mdt_webapp/images/example.png' %}')"></td>
                </tr>
                <tr class="content-table-row content-img-responsive show-700"><td class="content-table-data content-table-img" style="background-image: url('{% static 'mdt_webapp/images/example.png' %}')"></td></tr>
            </tbody>
        </table>
    </div>
    <div class="footer">
        If you encounter any issues with the site, please contact Callum Evans at:
        <br><a href="mailto:ce347@exeter.ac.uk"><i>ce347@exeter.ac.uk</i></a>
        <br><br><a href="http://localhost:8000/create/" style="font-size: small;">admin</a>
    </div>
</body>
</html>