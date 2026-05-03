# Northshore Logistics — Quick Run & Navigation

## Run

Prerequisite: Python 3.11+

From the repository root:

```bash
cd northshore_logistics
python main.py
```

The application will initialise the SQLite database and seed default users on first run.

## Default users

- admin / Admin123!
- manager / Manager123!
- warehouse / Warehouse123!
- driver / Driver123!
- service / Service123!

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
