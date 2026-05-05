import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import font as tkfont
from typing import Optional
import auth
import database
import audit
import reports
import security
import logging

logger = logging.getLogger('northshore.gui')

ROLE_PERMISSIONS = {
    'Admin': ['all'],
    'Manager': ['shipments', 'inventory', 'fleet', 'reports'],
    'Warehouse Staff': ['inventory', 'warehouse_activity'],
    'Driver': ['assigned_shipments'],
    'Customer Service': ['search_shipments', 'incidents', 'view_status']
}


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Northshore Logistics - Login')
        try:
            self.root.state('zoomed')
        except Exception:
            self.root.geometry('1000x700')
        self.root.minsize(800, 600)
        self.user = None
        self.role = None
        self.user_id = None
        self._build_login()

    def _build_login(self):
        for w in self.root.winfo_children():
            w.destroy()
        container = ttk.Frame(self.root, padding=20)
        container.pack(fill='both', expand=True)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=2)
        
        # Left: roles and counts
        left = ttk.Frame(container, padding=(10, 10))
        left.grid(row=0, column=0, sticky='nsew')
        ttk.Label(left, text='User Types', font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        self.roles_box = ttk.Frame(left)
        self.roles_box.pack(fill='both', expand=True, pady=(10, 0))
        self._populate_role_counts()

        # Right: login form
        right = ttk.Frame(container, padding=(20, 10))
        right.grid(row=0, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        ttk.Label(right, text='Welcome to Northshore Logistics', font=('Segoe UI', 18, 'bold')).grid(row=0, column=0, sticky='w', pady=(0,10))
        ttk.Label(right, text='Username').grid(row=1, column=0, sticky='w')
        self.username_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.username_var).grid(row=2, column=0, sticky='ew')
        ttk.Label(right, text='Password').grid(row=3, column=0, sticky='w', pady=(10,0))
        self.password_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.password_var, show='*').grid(row=4, column=0, sticky='ew')
        ttk.Button(right, text='Login', command=self._on_login).grid(row=5, column=0, pady=20, sticky='w')

        
        ttk.Label(right, text='Select a user type on the left to see how many users exist for that role.').grid(row=6, column=0, sticky='w')

    def _on_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        res = auth.verify_user(username, password)
        if res:
            self.user_id, self.user, role_id = res
            row = database.fetch_one('SELECT name FROM roles WHERE id = ?', (role_id,))
            self.role = row['name'] if row else 'Unknown'
            audit.audit(self.user_id, self.role, 'login', f'user {self.user} logged in')
            self._show_dashboard()
        else:
            audit.audit(None, 'Unknown', 'failed_login', f'username={username}')
            messagebox.showerror('Login failed', 'Invalid credentials')

    def _show_dashboard(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title(f'Northshore Logistics - {self.user} ({self.role})')
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill='both', expand=True)
        ttk.Label(frm, text=f'Welcome: {self.user}').grid(row=0, column=0, sticky='w')
        ttk.Button(frm, text='Change Password', command=self._change_password).grid(row=0, column=1, sticky='e')
        def _has_permission(perm: str) -> bool:
            role_name = (self.role or '').strip()
            if not role_name:
                return False
            perms = ROLE_PERMISSIONS.get(role_name)
            if perms is not None:
                return ('all' in perms) or (perm in perms)
            for k, v in ROLE_PERMISSIONS.items():
                if k.lower() == role_name.lower():
                    return ('all' in v) or (perm in v)
            return False

        col = 0
        def add_btn(text, cmd, perm):
            nonlocal col
            state = 'normal' if _has_permission(perm) else 'disabled'
            b = ttk.Button(frm, text=text, command=cmd, state=state)
            b.grid(row=1, column=col, padx=5, pady=5)
            col += 1

        add_btn('Shipments', self.open_shipments, 'shipments')
        add_btn('Inventory', self.open_inventory, 'inventory')
        add_btn('Fleet', self.open_fleet, 'fleet')
        add_btn('Drivers', self.open_drivers, 'fleet')
        add_btn('Incidents', self.open_incidents, 'incidents')
        add_btn('Reports', self.open_reports, 'reports')
        if self.role == 'Admin':
            ttk.Button(frm, text='Audit Logs', command=self.open_audit_logs).grid(row=2, column=0, pady=10)
        ttk.Button(frm, text='Logout', command=self.logout).grid(row=3, column=0, pady=10)

    def _change_password(self):
        """Allow user to change their password."""
        try:
            u = database.fetch_one('SELECT username FROM users WHERE id = ?', (self.user_id,))
            if not u:
                messagebox.showerror('Error', 'User not found')
                return
            username = u['username']
            cur_pwd = simpledialog.askstring('Current Password', 'Enter current password:', show='*', parent=self.root)
            if cur_pwd is None:
                return
            verified = auth.verify_user(username, cur_pwd)
            if not verified:
                messagebox.showerror('Error', 'Current password is incorrect')
                return
            new_pwd = simpledialog.askstring('New Password', 'Enter new password (min 8 chars):', show='*', parent=self.root)
            if new_pwd is None:
                return
            if len(new_pwd) < 8:
                messagebox.showerror('Error', 'Password must be at least 8 characters')
                return
            confirm = simpledialog.askstring('Confirm', 'Confirm new password:', show='*', parent=self.root)
            if confirm is None or confirm != new_pwd:
                messagebox.showerror('Error', 'Passwords do not match')
                return
            auth.update_password(self.user_id, new_pwd)
            messagebox.showinfo('Success', 'Password updated')
            audit.audit(self.user_id, self.role, 'change_password', 'user changed their password')
        except Exception as e:
            logger.exception('Change password failed')
            messagebox.showerror('Error', str(e))

    def logout(self):
        audit.audit(self.user_id, self.role, 'logout', f'user {self.user} logged out')
        self.user = None
        self.role = None
        self.user_id = None
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title('Northshore Logistics - Login')
        self._build_login()

    def _get_role_counts(self):
        try:
            rows = database.fetch_all('''
                SELECT r.id, r.name, COUNT(u.id) as count FROM roles r
                LEFT JOIN users u ON u.role_id = r.id
                GROUP BY r.id ORDER BY r.name
            ''')
            return rows
        except Exception:
            return []

    def _populate_role_counts(self):
        for w in getattr(self, 'roles_box', []).winfo_children() if hasattr(self, 'roles_box') else []:
            w.destroy()
        rows = self._get_role_counts()
        if not rows:
            if hasattr(self, 'roles_box'):
                ttk.Label(self.roles_box, text='No roles defined').pack(anchor='w')
            return
        # Map role display names to default usernames used by seeding
        role_to_username = {
            'Admin': 'admin',
            'Manager': 'manager',
            'Warehouse Staff': 'warehouse',
            'Driver': 'driver',
            'Customer Service': 'service'
        }
        for r in rows:
            text = f"{r['name']} — {r['count']} users"
            if hasattr(self, 'roles_box'):
                lbl = ttk.Label(self.roles_box, text=text, cursor='hand2')
                lbl.pack(anchor='w', pady=2)
                def _on_click(ev, role_name=r['name']):
                    uname = role_to_username.get(role_name, role_name.lower().replace(' ', '_'))
                    self.username_var.set(uname)
                lbl.bind('<Button-1>', _on_click)

    def open_shipments(self):
        win = tk.Toplevel(self.root)
        win.title('Shipments')
        frm = ttk.Frame(win, padding=10)
        frm.pack(fill='both', expand=True)
        ttk.Button(frm, text='Add Shipment', command=lambda: self.add_shipment(win)).grid(row=0, column=0, pady=5)
        ttk.Button(frm, text='Search Shipment', command=lambda: self.search_shipment(win)).grid(row=0, column=1, pady=5)
        ttk.Button(frm, text='Assign Driver/Vehicle', command=lambda: self.assign_resources(win)).grid(row=0, column=2, pady=5)

    def add_shipment(self, parent):
        dlg = tk.Toplevel(parent)
        dlg.title('Add Shipment')
        f = ttk.Frame(dlg, padding=10)
        f.pack()
        ttk.Label(f, text='Order Number').grid(row=0, column=0)
        on = tk.StringVar()
        ttk.Entry(f, textvariable=on).grid(row=0, column=1)
        ttk.Label(f, text='Customer ID').grid(row=1, column=0)
        cid = tk.StringVar()
        ttk.Entry(f, textvariable=cid).grid(row=1, column=1)
        ttk.Label(f, text='Origin Warehouse ID').grid(row=2, column=0)
        wid = tk.StringVar()
        ttk.Entry(f, textvariable=wid).grid(row=2, column=1)
        ttk.Label(f, text='Destination Address').grid(row=3, column=0)
        dest = tk.StringVar()
        ttk.Entry(f, textvariable=dest).grid(row=3, column=1)
        ttk.Label(f, text='Weight (kg)').grid(row=4, column=0)
        wt = tk.StringVar(value='0')
        ttk.Entry(f, textvariable=wt).grid(row=4, column=1)
        def submit():
            try:
                database.safe_execute('INSERT INTO shipments (order_number, customer_id, origin_warehouse, destination_address, weight, status) VALUES (?, ?, ?, ?, ?, ?)',
                                     (on.get(), int(cid.get()), int(wid.get()), dest.get(), float(wt.get()), 'Pending'))
                audit.audit(self.user_id, self.role, 'add_shipment', f'order={on.get()}')
                messagebox.showinfo('Success', 'Shipment added')
                dlg.destroy()
            except Exception as e:
                logger.exception('Failed add shipment')
                messagebox.showerror('Error', str(e))
        ttk.Button(f, text='Submit', command=submit).grid(row=5, column=0, columnspan=2, pady=10)

    def search_shipment(self, parent):
        q = simpledialog.askstring('Search', 'Enter order number or shipment ID')
        if not q:
            return
        rows = database.fetch_all('SELECT * FROM shipments WHERE order_number = ? OR id = ?', (q, q))
        if not rows:
            messagebox.showinfo('Not found', 'No shipment found')
            return
        for r in rows:
            self._show_shipment_detail(r)

    def _show_shipment_detail(self, row):
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Shipment {row['order_number']}")
        f = ttk.Frame(dlg, padding=10)
        f.pack()
        for i, (k, v) in enumerate(dict(row).items()):
            ttk.Label(f, text=f"{k}:").grid(row=i, column=0, sticky='w')
            ttk.Label(f, text=str(v)).grid(row=i, column=1, sticky='w')
        ttk.Button(f, text='Add Update', command=lambda: self.add_delivery_update(row['id'])).grid(row=0, column=2)
        ttk.Button(f, text='Add Incident', command=lambda: self.add_incident_for_shipment(row['id'])).grid(row=1, column=2)
        ttk.Button(f, text='Add Payment', command=lambda: self.add_payment_for_shipment(row['id'])).grid(row=2, column=2)

    def assign_resources(self, parent):
        sid = simpledialog.askinteger('Assign', 'Shipment ID')
        if not sid:
            return
        did = simpledialog.askinteger('Driver', 'Driver ID')
        vid = simpledialog.askinteger('Vehicle', 'Vehicle ID')
        try:
            database.safe_execute('UPDATE shipments SET assigned_driver = ?, assigned_vehicle = ?, status = ? , updated_at = datetime("now") WHERE id = ?', (did, vid, 'In Transit', sid))
            audit.audit(self.user_id, self.role, 'assign_resources', f'shipment={sid} driver={did} vehicle={vid}')
            messagebox.showinfo('Assigned', 'Driver and vehicle assigned')
        except Exception as e:
            logger.exception('Assign failed')
            messagebox.showerror('Error', str(e))

    def add_delivery_update(self, shipment_id):
        status = simpledialog.askstring('Status', 'Enter new status')
        note = simpledialog.askstring('Note', 'Optional note')
        if not status:
            return
        try:
            database.safe_execute('INSERT INTO delivery_updates (shipment_id, status, note) VALUES (?, ?, ?)', (shipment_id, status, note))
            database.safe_execute('UPDATE shipments SET status = ?, updated_at = datetime("now") WHERE id = ?', (status, shipment_id))
            audit.audit(self.user_id, self.role, 'update_shipment', f'id={shipment_id} status={status}')
            messagebox.showinfo('Updated', 'Delivery update added')
        except Exception as e:
            logger.exception('Failed add update')
            messagebox.showerror('Error', str(e))

    def add_incident_for_shipment(self, shipment_id):
        desc = simpledialog.askstring('Incident', 'Describe the incident')
        if not desc:
            return
        try:
            database.safe_execute('INSERT INTO incidents (shipment_id, reported_by, description) VALUES (?, ?, ?)', (shipment_id, self.user_id, desc))
            audit.audit(self.user_id, self.role, 'add_incident', f'shipment={shipment_id}')
            messagebox.showinfo('Done', 'Incident recorded')
        except Exception as e:
            logger.exception('Incident failed')
            messagebox.showerror('Error', str(e))

    def add_payment_for_shipment(self, shipment_id):
        amt = simpledialog.askfloat('Amount', 'Payment amount')
        method = simpledialog.askstring('Method', 'Payment method')
        ref = simpledialog.askstring('Reference', 'Payment reference')
        if amt is None:
            return
        try:
            ref_ob = security.obfuscate_reference(ref or '')
            database.safe_execute('INSERT INTO payments (shipment_id, amount, method, reference, status) VALUES (?, ?, ?, ?, ?)', (shipment_id, amt, method, ref_ob, 'Paid'))
            database.safe_execute('UPDATE shipments SET payment_status = ? WHERE id = ?', ('Paid', shipment_id))
            audit.audit(self.user_id, self.role, 'add_payment', f'shipment={shipment_id} amount={amt}')
            messagebox.showinfo('Done', 'Payment recorded')
        except Exception as e:
            logger.exception('Payment failed')
            messagebox.showerror('Error', str(e))

    def open_inventory(self):
        win = tk.Toplevel(self.root)
        win.title('Inventory')
        f = ttk.Frame(win, padding=10)
        f.pack()
        ttk.Button(f, text='Add Item', command=self.add_inventory_item).grid(row=0, column=0)
        ttk.Button(f, text='Update Stock', command=self.update_stock).grid(row=0, column=1)
        ttk.Button(f, text='View Low Stock', command=self.view_low_stock).grid(row=0, column=2)

    def add_inventory_item(self):
        name = simpledialog.askstring('Name', 'Item name')
        sku = simpledialog.askstring('SKU', 'SKU')
        desc = simpledialog.askstring('Description', 'Description')
        reorder = simpledialog.askinteger('Reorder', 'Reorder level', initialvalue=5)
        if not name or not sku:
            return
        try:
            database.safe_execute('INSERT INTO inventory_items (sku, name, description, reorder_level) VALUES (?, ?, ?, ?)', (sku, name, desc, reorder))
            audit.audit(self.user_id, self.role, 'add_inventory', f'sku={sku}')
            messagebox.showinfo('Added', 'Item added')
        except Exception as e:
            logger.exception('Add item failed')
            messagebox.showerror('Error', str(e))

    def update_stock(self):
        item_id = simpledialog.askinteger('Item ID', 'Item ID')
        ware_id = simpledialog.askinteger('Warehouse ID', 'Warehouse ID')
        qty = simpledialog.askinteger('Quantity', 'Quantity to set')
        if not item_id or not ware_id:
            return
        try:
            exists = database.fetch_one('SELECT id FROM inventory_stock WHERE item_id = ? AND warehouse_id = ?', (item_id, ware_id))
            if exists:
                database.safe_execute('UPDATE inventory_stock SET quantity = ?, last_updated = datetime("now") WHERE id = ?', (qty, exists['id']))
            else:
                database.safe_execute('INSERT INTO inventory_stock (item_id, warehouse_id, quantity) VALUES (?, ?, ?)', (item_id, ware_id, qty))
            database.safe_execute('INSERT INTO warehouse_activity (warehouse_id, item_id, quantity, activity_type, note) VALUES (?, ?, ?, ?, ?)', (ware_id, item_id, qty, 'INBOUND', 'Manual update'))
            audit.audit(self.user_id, self.role, 'update_stock', f'item={item_id} warehouse={ware_id} qty={qty}')
            messagebox.showinfo('Updated', 'Stock updated')
        except Exception as e:
            logger.exception('Update stock error')
            messagebox.showerror('Error', str(e))

    def view_low_stock(self):
        rows = database.fetch_all('''
            SELECT i.id, i.sku, i.name, s.warehouse_id, s.quantity, i.reorder_level FROM inventory_items i
            JOIN inventory_stock s ON i.id = s.item_id
            WHERE s.quantity <= i.reorder_level
        ''')
        if not rows:
            messagebox.showinfo('Low stock', 'No low stock items')
            return
        txt = '\n'.join([f"{r['sku']} - {r['name']} (WH {r['warehouse_id']} qty={r['quantity']})" for r in rows])
        messagebox.showinfo('Low stock', txt)

    def open_fleet(self):
        win = tk.Toplevel(self.root)
        win.title('Fleet')
        f = ttk.Frame(win, padding=10)
        f.pack()
        ttk.Button(f, text='Add Vehicle', command=self.add_vehicle).grid(row=0, column=0)
        ttk.Button(f, text='Update Availability', command=self.update_vehicle_availability).grid(row=0, column=1)

    def add_vehicle(self):
        reg = simpledialog.askstring('Registration', 'Registration')
        model = simpledialog.askstring('Model', 'Model')
        cap = simpledialog.askinteger('Capacity', 'Capacity kg', initialvalue=1000)
        if not reg:
            return
        try:
            database.safe_execute('INSERT INTO vehicles (registration, model, capacity, available) VALUES (?, ?, ?, ?)', (reg, model, cap, 1))
            audit.audit(self.user_id, self.role, 'add_vehicle', f'reg={reg}')
            messagebox.showinfo('Added', 'Vehicle added')
        except Exception as e:
            logger.exception('Add vehicle')
            messagebox.showerror('Error', str(e))

    def update_vehicle_availability(self):
        vid = simpledialog.askinteger('Vehicle ID', 'Vehicle ID')
        avail = simpledialog.askinteger('Available?', '1=available,0=not', initialvalue=1)
        if vid is None:
            return
        try:
            database.safe_execute('UPDATE vehicles SET available = ? WHERE id = ?', (1 if avail else 0, vid))
            audit.audit(self.user_id, self.role, 'update_vehicle', f'vehicle={vid} available={avail}')
            messagebox.showinfo('Updated', 'Vehicle updated')
        except Exception as e:
            logger.exception('Update vehicle')
            messagebox.showerror('Error', str(e))

    def open_drivers(self):
        win = tk.Toplevel(self.root)
        win.title('Drivers')
        f = ttk.Frame(win, padding=10)
        f.pack()
        ttk.Button(f, text='Add Driver', command=self.add_driver).grid(row=0, column=0)
        ttk.Button(f, text='Assign Shift', command=self.assign_shift).grid(row=0, column=1)

    def add_driver(self):
        name = simpledialog.askstring('Name', 'Driver name')
        phone = simpledialog.askstring('Phone', 'Phone')
        lic = simpledialog.askstring('License', 'License number')
        if not name:
            return
        try:
            masked = security.mask_personal(name, phone)
            database.safe_execute('INSERT INTO drivers (name, phone, license_number, details_masked) VALUES (?, ?, ?, ?)', (name, phone, lic, masked))
            audit.audit(self.user_id, self.role, 'add_driver', f'name={name}')
            messagebox.showinfo('Added', 'Driver added')
        except Exception as e:
            logger.exception('Add driver')
            messagebox.showerror('Error', str(e))

    def assign_shift(self):
        did = simpledialog.askinteger('Driver ID', 'Driver ID')
        start = simpledialog.askstring('Start', 'Shift start (YYYY-MM-DD HH:MM)')
        end = simpledialog.askstring('End', 'Shift end (optional)')
        if not did or not start:
            return
        try:
            database.safe_execute('INSERT INTO driver_shifts (driver_id, shift_start, shift_end) VALUES (?, ?, ?)', (did, start, end))
            audit.audit(self.user_id, self.role, 'assign_shift', f'driver={did} start={start}')
            messagebox.showinfo('Assigned', 'Shift assigned')
        except Exception as e:
            logger.exception('Assign shift')
            messagebox.showerror('Error', str(e))

    def open_incidents(self):
        win = tk.Toplevel(self.root)
        win.title('Incidents')
        f = ttk.Frame(win, padding=10)
        f.pack()
        ttk.Button(f, text='Report Incident', command=self.report_incident).grid(row=0, column=0)
        ttk.Button(f, text='View Incidents', command=self.view_incidents).grid(row=0, column=1)

    def report_incident(self):
        sid = simpledialog.askinteger('Shipment ID', 'Shipment ID (optional)')
        desc = simpledialog.askstring('Description', 'Describe incident')
        if not desc:
            return
        try:
            database.safe_execute('INSERT INTO incidents (shipment_id, reported_by, description) VALUES (?, ?, ?)', (sid, self.user_id, desc))
            audit.audit(self.user_id, self.role, 'add_incident', f'shipment={sid}')
            messagebox.showinfo('Done', 'Incident recorded')
        except Exception as e:
            logger.exception('Report incident')
            messagebox.showerror('Error', str(e))

    def view_incidents(self):
        rows = database.fetch_all('SELECT id, shipment_id, description, resolved, created_at FROM incidents')
        if not rows:
            messagebox.showinfo('Incidents', 'No incidents')
            return
        txt = '\n'.join([f"{r['id']}: shipment={r['shipment_id']} resolved={r['resolved']} {r['description']}" for r in rows])
        messagebox.showinfo('Incidents', txt)

    def open_reports(self):
        win = tk.Toplevel(self.root)
        win.title('Reports')
        f = ttk.Frame(win, padding=10)
        f.pack()
        ttk.Button(f, text='Delivery Progress', command=lambda: self._run_report(reports.delivery_progress_report)).grid(row=0, column=0)
        ttk.Button(f, text='Delayed Shipments', command=lambda: self._run_report(reports.delayed_shipments_report)).grid(row=0, column=1)
        ttk.Button(f, text='Warehouse Activity', command=lambda: self._run_report(reports.warehouse_activity_report)).grid(row=1, column=0)
        ttk.Button(f, text='Low Stock', command=lambda: self._run_report(reports.low_stock_report)).grid(row=1, column=1)
        ttk.Button(f, text='Vehicle Utilisation', command=lambda: self._run_report(reports.vehicle_utilisation_report)).grid(row=2, column=0)
        ttk.Button(f, text='Incidents', command=lambda: self._run_report(reports.incident_resolution_report)).grid(row=2, column=1)
        ttk.Button(f, text='Payments', command=lambda: self._run_report(reports.payment_status_report)).grid(row=3, column=0)

    def _run_report(self, func):
        try:
            path = func(self.user_id or 0, self.role or 'Unknown')
            messagebox.showinfo('Report', f'Report exported to {path}')
        except Exception as e:
            logger.exception('Report failed')
            messagebox.showerror('Error', str(e))

    def open_audit_logs(self):
        rows = database.fetch_all('SELECT a.id, u.username, a.role, a.action, a.details, a.timestamp FROM audit_logs a LEFT JOIN users u ON a.user_id = u.id ORDER BY a.timestamp DESC LIMIT 200')
        if not rows:
            messagebox.showinfo('Audit', 'No audit logs')
            return
        txt = '\n'.join([f"{r['timestamp']} - {r['username'] or 'Unknown'} - {r['action']} - {r['details']}" for r in rows])
        dlg = tk.Toplevel(self.root)
        dlg.title('Audit Logs')
        t = tk.Text(dlg, wrap='none', width=120, height=30)
        t.pack(fill='both', expand=True)
        t.insert('1.0', txt)


def launch():
    root = tk.Tk()
    app = App(root)
    root.mainloop()
