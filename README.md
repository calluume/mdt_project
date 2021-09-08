# Manchester Digital Twin Project
This is a basic digital twin of the central Manchester wards of Deansgate and Piccadilly, that is able to simulate emissions levels from traffic. A fully deployed version of the system can also be viewed at [manchester-dt.co.uk](http://manchester-dt.co.uk/).

## Project Dependencies
The system has the following python dependencies:

Django, Folium, Plotly, overpy, numpy, sklearn, geopy, shapely, pandas

## Usage
To view the project by creating a development server:
1. Relocate to the mdt_project file and run the command below. The ```-b``` flag can be used to specify a different IP address and port. In case of 'file not found' errors during startup, the input directory for calculating emissions may be found [here](https://github.com/pollemission/pollemission), and replaces mdt_webapp/mdt/pollemission/input.

```python3 manage.py runserver```

2. Open a browser and go to localhost:8000. This will direct you to the landing page with links to each map.

To create a network through the NetworkCreator page:
1. Create a superuser with the command:

```python3 manage.py createsuperuser```

2. Follow the instructions by entering an admin username, password and email.
3. Open a browser and go to localhost:8000/admin/, and enter your username and password.
4. Either go to localhost:8000/create/ or follow the admin link in the footer of the landing page.
5. Select the networks to create, and click create. The progress can be followed on the console.
6. Once done, the resulting object files will be stored at mdt_webapp/mdt/obj.
