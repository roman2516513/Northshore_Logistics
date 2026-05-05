# Northshore Logistics — Quick Run & Navigation

## Run

Prerequisite: Python 3.11+

From the repository root:

```bash

cd northshore_logistics


python main.py


```

The application will initialise the SQLite database and seed default roles on first run.

## Initial Credentials (Local/Dev)

Hard-coded credentials for testing:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | Admin123! |
| Manager | manager | Manager123! |
| Warehouse Staff | warehouse | Warehouse123! |
| Driver | driver | Driver123! |
| Customer Service | service | Service123! |

**⚠️ IMPORTANT:** Change these passwords immediately after first login using the "Change Password" button on the dashboard. Do NOT deploy with these credentials to production.

## Workflow

A short, typical workflow:

- Login using one of the seeded users.
- From the dashboard open the relevant area (Shipments, Inventory, Fleet, Drivers, Incidents).
- Create or update records using the provided dialogs and buttons.
- Use Reports to export CSVs for analysis.
- Admin users can view Audit Logs for activity tracking.

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
