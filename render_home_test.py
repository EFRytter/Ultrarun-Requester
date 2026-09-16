"""
Small helper to render `home.html` using Jinja2 outside the Flask
application context. This is useful for catching template syntax errors
or for quick local preview during development without running the web
server.

What it does:
- Configures a Jinja2 environment pointing at the `templates/`
    directory.
- Stubs `url_for` and `get_flashed_messages` globals used by the
    templates so rendering works without Flask.
- Creates simple `Run` and `Station` objects and renders
    `home.html` with empty item lists.

Run this script from the project root to see the rendered HTML on
stdout.
"""

from jinja2 import Environment, FileSystemLoader, StrictUndefined
import os

# Setup loader pointing to templates directory
here = os.path.dirname(__file__)
loader = FileSystemLoader(os.path.join(here, 'templates'))
env = Environment(loader=loader, undefined=StrictUndefined)

# Provide a dummy url_for and get_flashed_messages to avoid Flask
env.globals['url_for'] = lambda endpoint, **kwargs: f'/{endpoint}'
env.globals['get_flashed_messages'] = lambda: []

# Dummy objects used to render the template
class Run:
        def __init__(self, id):
                self.id = id

class Station:
        def __init__(self, id, name, distance, station_number):
                self.id = id
                self.name = name
                self.distance = distance
                self.station_number = station_number

run = Run(1)
stations = [Station(1, 'Start', 0.0, 1), Station(2, 'Mid', 5.5, 2), Station(3, 'End', 11.0, 3)]

template = env.get_template('home.html')
print(template.render(run=run, stations=stations, food=[], liquids=[], other=[]))
