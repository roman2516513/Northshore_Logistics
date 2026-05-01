PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT,
    role_id INTEGER NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_phone TEXT,
    contact_email TEXT,
    address TEXT NOT NULL
);

