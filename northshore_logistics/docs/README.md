# Northshore Logistics — Quick Run & Navigation

## Run

Prerequisite: Python 3.11+

From the repository root:

```bash

cd northshore_logistics


python main.py


```

The application will initialise the SQLite database and seed default roles on first run.

An initial administrative account will be created automatically if no users exist. A randomly generated password
will be written to a local file named `northshore_local_credentials.txt` (or `<dbname>.credentials.txt` next to the database).
Keep that file private and remove it after you set a permanent password. The repository does NOT contain default plaintext credentials.

## Navigate

- Login using one of the default users above.
- Shipments: Add Shipment, Search Shipment, Assign Driver/Vehicle.
- Inventory: Add Item, Update Stock, View Low Stock.
- Fleet: Add Vehicle, Update Availability.
- Drivers: Add Driver, Assign Shift.
- Incidents: Report Incident, View Incidents.
- Reports: Export Delivery Progress, Delayed Shipments, Warehouse Activity, Low Stock, Vehicle Utilisation, Incidents, Payments (CSV).
- Audit Logs: available to Admin users.

For GUI actions, follow on-screen dialogs and prompts.
