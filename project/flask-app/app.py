from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

DATABASE = 'inventory.db'

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT ''
        )
    ''')

    # Create locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            location_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT DEFAULT ''
        )
    ''')

    # Create product_movements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_movements (
            movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            from_location TEXT,
            to_location TEXT,
            product_id TEXT NOT NULL,
            qty INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
            FOREIGN KEY (from_location) REFERENCES locations(location_id) ON DELETE CASCADE,
            FOREIGN KEY (to_location) REFERENCES locations(location_id) ON DELETE CASCADE,
            CHECK (from_location IS NOT NULL OR to_location IS NOT NULL)
        )
    ''')

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Product routes
@app.route('/products')
def products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY product_id').fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        name = request.form['name']
        description = request.form['description']

        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO products (product_id, name, description) VALUES (?, ?, ?)',
                        (product_id, name, description))
            conn.commit()
            conn.close()
            flash('Product added successfully!', 'success')
            return redirect(url_for('products'))
        except sqlite3.IntegrityError:
            flash('Product ID already exists!', 'error')

    return render_template('product_form.html', product=None, action='Add')

@app.route('/products/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        conn.execute('UPDATE products SET name = ?, description = ? WHERE product_id = ?',
                    (name, description, product_id))
        conn.commit()
        conn.close()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))

    conn.close()
    return render_template('product_form.html', product=product, action='Edit')

@app.route('/products/delete/<product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
    conn.commit()
    conn.close()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products'))

# Location routes
@app.route('/locations')
def locations():
    conn = get_db_connection()
    locations = conn.execute('SELECT * FROM locations ORDER BY location_id').fetchall()
    conn.close()
    return render_template('locations.html', locations=locations)

@app.route('/locations/add', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        location_id = request.form['location_id']
        name = request.form['name']
        address = request.form['address']

        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO locations (location_id, name, address) VALUES (?, ?, ?)',
                        (location_id, name, address))
            conn.commit()
            conn.close()
            flash('Location added successfully!', 'success')
            return redirect(url_for('locations'))
        except sqlite3.IntegrityError:
            flash('Location ID already exists!', 'error')

    return render_template('location_form.html', location=None, action='Add')

@app.route('/locations/edit/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    conn = get_db_connection()
    location = conn.execute('SELECT * FROM locations WHERE location_id = ?', (location_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']

        conn.execute('UPDATE locations SET name = ?, address = ? WHERE location_id = ?',
                    (name, address, location_id))
        conn.commit()
        conn.close()
        flash('Location updated successfully!', 'success')
        return redirect(url_for('locations'))

    conn.close()
    return render_template('location_form.html', location=location, action='Edit')

@app.route('/locations/delete/<location_id>', methods=['POST'])
def delete_location(location_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM locations WHERE location_id = ?', (location_id,))
    conn.commit()
    conn.close()
    flash('Location deleted successfully!', 'success')
    return redirect(url_for('locations'))

# Product Movement routes
@app.route('/movements')
def movements():
    conn = get_db_connection()
    movements = conn.execute('''
        SELECT m.*, p.name as product_name,
               fl.name as from_loc_name, tl.name as to_loc_name
        FROM product_movements m
        JOIN products p ON m.product_id = p.product_id
        LEFT JOIN locations fl ON m.from_location = fl.location_id
        LEFT JOIN locations tl ON m.to_location = tl.location_id
        ORDER BY m.timestamp DESC
    ''').fetchall()
    conn.close()
    return render_template('movements.html', movements=movements)

@app.route('/movements/add', methods=['GET', 'POST'])
def add_movement():
    conn = get_db_connection()

    if request.method == 'POST':
        product_id = request.form['product_id']
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        qty = request.form['qty']

        if not from_location and not to_location:
            flash('Either from_location or to_location must be specified!', 'error')
        else:
            conn.execute('''
                INSERT INTO product_movements (product_id, from_location, to_location, qty)
                VALUES (?, ?, ?, ?)
            ''', (product_id, from_location, to_location, qty))
            conn.commit()
            flash('Movement added successfully!', 'success')
            conn.close()
            return redirect(url_for('movements'))

    products = conn.execute('SELECT * FROM products ORDER BY name').fetchall()
    locations = conn.execute('SELECT * FROM locations ORDER BY name').fetchall()
    conn.close()
    return render_template('movement_form.html', movement=None, products=products,
                         locations=locations, action='Add')

@app.route('/movements/edit/<int:movement_id>', methods=['GET', 'POST'])
def edit_movement(movement_id):
    conn = get_db_connection()
    movement = conn.execute('SELECT * FROM product_movements WHERE movement_id = ?',
                          (movement_id,)).fetchone()

    if request.method == 'POST':
        product_id = request.form['product_id']
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        qty = request.form['qty']

        if not from_location and not to_location:
            flash('Either from_location or to_location must be specified!', 'error')
        else:
            conn.execute('''
                UPDATE product_movements
                SET product_id = ?, from_location = ?, to_location = ?, qty = ?
                WHERE movement_id = ?
            ''', (product_id, from_location, to_location, qty, movement_id))
            conn.commit()
            flash('Movement updated successfully!', 'success')
            conn.close()
            return redirect(url_for('movements'))

    products = conn.execute('SELECT * FROM products ORDER BY name').fetchall()
    locations = conn.execute('SELECT * FROM locations ORDER BY name').fetchall()
    conn.close()
    return render_template('movement_form.html', movement=movement, products=products,
                         locations=locations, action='Edit')

@app.route('/movements/delete/<int:movement_id>', methods=['POST'])
def delete_movement(movement_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM product_movements WHERE movement_id = ?', (movement_id,))
    conn.commit()
    conn.close()
    flash('Movement deleted successfully!', 'success')
    return redirect(url_for('movements'))

# Balance Report route
@app.route('/report')
def report():
    conn = get_db_connection()

    # Calculate balance: incoming - outgoing for each product-location combination
    balance_query = '''
        WITH incoming AS (
            SELECT product_id, to_location as location_id, SUM(qty) as qty_in
            FROM product_movements
            WHERE to_location IS NOT NULL
            GROUP BY product_id, to_location
        ),
        outgoing AS (
            SELECT product_id, from_location as location_id, SUM(qty) as qty_out
            FROM product_movements
            WHERE from_location IS NOT NULL
            GROUP BY product_id, from_location
        ),
        all_combinations AS (
            SELECT DISTINCT product_id, location_id FROM (
                SELECT product_id, to_location as location_id FROM product_movements WHERE to_location IS NOT NULL
                UNION
                SELECT product_id, from_location as location_id FROM product_movements WHERE from_location IS NOT NULL
            )
        )
        SELECT
            ac.product_id,
            p.name as product_name,
            ac.location_id,
            l.name as location_name,
            COALESCE(i.qty_in, 0) - COALESCE(o.qty_out, 0) as balance
        FROM all_combinations ac
        JOIN products p ON ac.product_id = p.product_id
        JOIN locations l ON ac.location_id = l.location_id
        LEFT JOIN incoming i ON ac.product_id = i.product_id AND ac.location_id = i.location_id
        LEFT JOIN outgoing o ON ac.product_id = o.product_id AND ac.location_id = o.location_id
        ORDER BY p.name, l.name
    '''

    balances = conn.execute(balance_query).fetchall()
    conn.close()
    return render_template('report.html', balances=balances)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
