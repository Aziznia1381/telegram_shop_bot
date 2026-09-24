import sqlite3


DATABASE_NAME = "shop.db"


def connect():
    return sqlite3.connect(DATABASE_NAME)


def create_tables():

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            products TEXT NOT NULL,
            total INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()


def save_order(
    name,
    phone,
    address,
    products,
    total
):

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO orders
        (name, phone, address, products, total, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        phone,
        address,
        products,
        total,
        "جدید"
    ))

    connection.commit()

    order_id = cursor.lastrowid

    connection.close()

    return order_id


def get_orders():

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            phone,
            address,
            products,
            total,
            status,
            created_at
        FROM orders
        ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    connection.close()

    return orders


def get_order(order_id):

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            phone,
            address,
            products,
            total,
            status,
            created_at
        FROM orders
        WHERE id = ?
    """, (order_id,))

    order = cursor.fetchone()

    connection.close()

    return order


def update_order_status(order_id, status):

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE orders
        SET status = ?
        WHERE id = ?
    """, (status, order_id))

    connection.commit()

    connection.close()


def delete_order(order_id):

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM orders
        WHERE id = ?
    """, (order_id,))

    connection.commit()

    connection.close()