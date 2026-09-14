
# 100 Miles Food Requester
A web application for ultrarunners and their crew members to plan and communicate food, drink, and hygiene needs at upcoming aid/deposit stations.

# Purpose
During a long-distance run, runners may need different supplies at each station. This website lets a runner select what they want at each upcoming station, while crew members see the same requests immediately and can prepare the correct items.

# Users
Runner: Selects required supplies for each station.
Crew member: Views the runner’s selected supplies and uses the list to prepare station bags or handovers.

Shared access: The app is designed so multiple people can open it online during the event.

# Main features
Station setup
Users can create stations for a specific run. Each station includes:
* Station name
* Address or location
* Mileage or distance point in the race
* Order in the route
Stations are shown in mileage order as a timeline across the top of the page, giving users a clear overview of upcoming stops.

# Runner view
The runner view shows the selected station and three supply categories:
* Food
* Liquids
* Hygiene items
Each category contains a checklist of available items. The runner selects an item by ticking its checkbox.

A selection is connected to one specific station. For example, a runner may request soup and cola at Station 3, but only water and sunscreen at Station 4.

# Crew view
The crew view displays the same station timeline and selected supply lists.
An item selected by the runner is visually marked with a green background.
Items not selected remain unmarked.
The crew member can quickly switch between stations to prepare the correct supplies.
The runner and crew views show the same saved data, but present it differently: the runner edits selections, while the crew mainly reads them.

# Saving requests
Every selected item must be saved in the SQL database together with the station it belongs to.
When a runner ticks an item, the app creates and saves a selection for that station.
When a runner unticks an item, the saved selection is deleted.
The crew view reads the latest saved selections from the database.
This means the app does not rely on temporary Python lists, which disappear when the server restarts; instead, selections remain available online for both runners and crew.

# Live updates
The crew page should refresh automatically at a regular interval so newly selected items become visible without the crew member manually reloading the page. A later improvement could use real-time updates, but automatic refresh is the simplest reliable first version.