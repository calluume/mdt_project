<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Access Denied</title>
    {% load static %}
    <link rel="preconnect" href="https://fonts.gstatic.com">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100;300;400;500;700;900&display=swap" rel="stylesheet">
    <link rel="icon" type="image/png" href="{% static 'mdt_webapp/images/fav.png' %}">
    <link rel="stylesheet" type="text/css" href="{% static 'mdt_webapp/simple.css' %}">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>

    </style>
</head>
<body>
    <div>
        <h2>
            Access denied<br><a href="http://localhost:8000">Return to the homepage</a>
        </h2>
        <a href="http://localhost:8000/create/" id="retry">Retry</a>
    </div>
</body>
</html>