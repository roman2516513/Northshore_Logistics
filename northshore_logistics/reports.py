import os
import csv
import database
import audit

try:
    import pandas as pd
    _HAS_PANDAS = True
except Exception:
    pd = None
    _HAS_PANDAS = False

BASE_DIR = os.path.dirname(__file__)
EXPORT_DIR = os.path.join(BASE_DIR, 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)


def _to_csv(rows, filename: str):
    path = os.path.join(EXPORT_DIR, filename)
    if _HAS_PANDAS:
        if not rows:
            df = pd.DataFrame()
        else:
            df = pd.DataFrame([dict(r) for r in rows])
        df.to_csv(path, index=False)
        return path
    # fallback to csv
    if not rows:
        with open(path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow([])
        return path
    fieldnames = list(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(dict(r))
    return path


def delivery_progress_report(user_id: int, role: str) -> str:
    rows = database.fetch_all('SELECT id, order_number, status, expected_delivery, updated_at FROM shipments')
    path = _to_csv(rows, 'delivery_progress_report.csv')
    audit.audit(user_id, role, 'generate_report', 'delivery_progress')
    return path


def delayed_shipments_report(user_id: int, role: str) -> str:
    rows = database.fetch_all("SELECT id, order_number, status, expected_delivery FROM shipments WHERE status = 'Delayed'")
    path = _to_csv(rows, 'delayed_shipments_report.csv')
    audit.audit(user_id, role, 'generate_report', 'delayed_shipments')
    return path


def warehouse_activity_report(user_id: int, role: str) -> str:
    rows = database.fetch_all('SELECT * FROM warehouse_activity')
    path = _to_csv(rows, 'warehouse_activity_report.csv')
    audit.audit(user_id, role, 'generate_report', 'warehouse_activity')
    return path


def low_stock_report(user_id: int, role: str) -> str:
    rows = database.fetch_all('''
        SELECT i.sku, i.name, s.warehouse_id, s.quantity, i.reorder_level
        FROM inventory_items i
        JOIN inventory_stock s ON i.id = s.item_id
        WHERE s.quantity <= i.reorder_level
    ''')
    path = _to_csv(rows, 'low_stock_report.csv')
    audit.audit(user_id, role, 'generate_report', 'low_stock')
    return path


def vehicle_utilisation_report(user_id: int, role: str) -> str:
    rows = database.fetch_all('SELECT v.id, v.registration, v.model, v.available FROM vehicles v')
    path = _to_csv(rows, 'vehicle_utilisation_report.csv')
    audit.audit(user_id, role, 'generate_report', 'vehicle_utilisation')
    return path


def incident_resolution_report(user_id: int, role: str) -> str:
    rows = database.fetch_all('SELECT id, shipment_id, description, resolved, created_at, resolved_at FROM incidents')
    path = _to_csv(rows, 'incident_resolution_report.csv')
    audit.audit(user_id, role, 'generate_report', 'incident_resolution')
    return path


def payment_status_report(user_id: int, role: str) -> str:
    rows = database.fetch_all('SELECT id, shipment_id, amount, status, created_at FROM payments')
    path = _to_csv(rows, 'payment_status_report.csv')
    audit.audit(user_id, role, 'generate_report', 'payment_status')
    return path
