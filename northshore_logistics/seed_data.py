import database
import auth
import security
import os
import logging

logger = logging.getLogger('northshore.seed')


def seed_if_empty() -> None:
    auth.ensure_default_users()
    wh = database.fetch_one('SELECT id FROM warehouses LIMIT 1')
    if wh:
        logger.info('Database already seeded (warehouses present)')
        return
    warehouses = [
        ('Central Warehouse', '10 Harbor Road, Northshore', 10000),
        ('North Depot', '22 Elm Street, Northshore', 5000)
    ]
    for name, loc, cap in warehouses:
        database.safe_execute('INSERT INTO warehouses (name, location, capacity) VALUES (?, ?, ?)', (name, loc, cap))
    customers = [
        ('Alice Logistics', '0411000111', 'alice@example.com', security.mask_address('100 Alice Lane, Northshore City')),
        ('Beta Trading', '0411222333', 'beta@example.com', security.mask_address('200 Beta Road, Northshore City'))
    ]
    for c in customers:
        database.safe_execute('INSERT INTO customers (name, contact_phone, contact_email, address) VALUES (?, ?, ?, ?)', c)
    items = [
        ('SKU-1001', 'Blue Widgets', 'Small blue widgets', 10),
        ('SKU-1002', 'Red Widgets', 'Small red widgets', 8)
    ]
    for sku, name, desc, reorder in items:
        database.safe_execute('INSERT INTO inventory_items (sku, name, description, reorder_level) VALUES (?, ?, ?, ?)', (sku, name, desc, reorder))
    item_rows = database.fetch_all('SELECT id FROM inventory_items')
    wh_rows = database.fetch_all('SELECT id FROM warehouses')
    if item_rows and wh_rows:
        pairs = []
        for item in item_rows:
            for w in wh_rows:
                pairs.append((item['id'], w['id'], 50))
        database.safe_execute_many('INSERT INTO inventory_stock (item_id, warehouse_id, quantity) VALUES (?, ?, ?)', pairs)
    vehicles = [
        ('NS-001', 'Isuzu NLR', 1500, 1, None),
        ('NS-002', 'Hino 300', 3000, 1, None)
    ]
    for reg, model, cap, avail, maint in vehicles:
        database.safe_execute('INSERT INTO vehicles (registration, model, capacity, available, last_maintenance) VALUES (?, ?, ?, ?, ?)', (reg, model, cap, avail, maint))
    drivers = [
        ('John Doe', '0400111222', 'LIC12345'),
        ('Jane Smith', '0400333444', 'LIC67890')
    ]
    for name, phone, lic in drivers:
        masked = security.mask_personal(name, phone)
        database.safe_execute('INSERT INTO drivers (name, phone, license_number, details_masked) VALUES (?, ?, ?, ?)', (name, phone, lic, masked))
    cust = database.fetch_one('SELECT id FROM customers LIMIT 1')
    wh0 = database.fetch_one('SELECT id FROM warehouses LIMIT 1')
    if cust and wh0:
        database.safe_execute(
            'INSERT INTO shipments (order_number, customer_id, origin_warehouse, destination_address, weight, status, payment_status) VALUES (?, ?, ?, ?, ?, ?, ?)',
            ('ORD-1001', cust['id'], wh0['id'], '400 Customer Way, Northshore', 12.5, 'Pending', 'Pending')
        )
    logger.info('Seeded sample data')
