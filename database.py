import sqlite3

DATABASE = 'fieldops.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()

    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        password TEXT NOT NULL
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS electricians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        specialization TEXT,
        status TEXT DEFAULT 'Active',
        rating REAL DEFAULT 0.0
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        location TEXT,
        deadline TEXT,
        electrician_id INTEGER,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY (electrician_id) REFERENCES electricians(id)
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        job_id INTEGER,
        electrician_id INTEGER,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (electrician_id) REFERENCES electricians(id)
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        used INTEGER DEFAULT 0,
        unit TEXT DEFAULT 'pcs'
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL
    )''')

    db.commit()
    db.close()