"""Shared sample tables for the MySQL module.

Each dataset is defined once as Python rows; from that we generate
(1) the hidden SQL setup passed to sqlrun(..., setup=...) and
(2) a 'Sample Data' card so students can see the input rows.
"""
from build import card, table, p

def _lit(v):
    if v is None:
        return 'NULL'
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"

TABLES = {
    'departments': dict(
        ddl='dept_id INT PRIMARY KEY, dept_name VARCHAR(40) NOT NULL',
        cols=['dept_id', 'dept_name'],
        rows=[(10, 'Data Engineering'), (20, 'Analytics'), (30, 'HR'), (40, 'Marketing')]),
    'employees': dict(
        ddl=('emp_id INT PRIMARY KEY, name VARCHAR(40) NOT NULL, dept_id INT, manager_id INT, '
             'salary DECIMAL(10,2) NOT NULL, hire_date DATE NOT NULL, city VARCHAR(30)'),
        cols=['emp_id', 'name', 'dept_id', 'manager_id', 'salary', 'hire_date', 'city'],
        rows=[
            (1, 'Arjun', 10, None, 150000, '2018-04-01', 'Mumbai'),
            (2, 'Priya', 10, 1, 120000, '2019-07-15', 'Pune'),
            (3, 'Rahul', 10, 2, 95000, '2021-01-10', 'Mumbai'),
            (4, 'Sneha', 10, 2, 95000, '2022-03-01', 'Bengaluru'),
            (5, 'Vikram', 20, 1, 110000, '2019-02-20', 'Mumbai'),
            (6, 'Anjali', 20, 5, 82000, '2020-11-05', 'Pune'),
            (7, 'Karan', 20, 5, 115000, '2023-06-12', 'Delhi'),
            (8, 'Meera', 30, 1, 70000, '2017-09-30', 'Mumbai'),
            (9, 'Rohit', 30, 8, 52000, '2024-01-08', 'Pune'),
            (10, 'Divya', None, 1, 60000, '2025-05-19', 'Delhi'),
        ]),
    'customers': dict(
        ddl='customer_id INT PRIMARY KEY, name VARCHAR(40) NOT NULL, city VARCHAR(30), signup_date DATE',
        cols=['customer_id', 'name', 'city', 'signup_date'],
        rows=[(1, 'Asha', 'Mumbai', '2025-11-02'), (2, 'Ravi', 'Pune', '2025-12-15'), (3, 'Neha', 'Delhi', '2026-01-05'),
              (4, 'Imran', 'Mumbai', '2026-01-20'), (5, 'Pooja', 'Bengaluru', '2026-02-11'), (6, 'Tarun', 'Pune', '2026-03-01')]),
    'products': dict(
        ddl='product_id INT PRIMARY KEY, name VARCHAR(40) NOT NULL, category VARCHAR(20), price DECIMAL(10,2)',
        cols=['product_id', 'name', 'category', 'price'],
        rows=[(1, 'Laptop', 'Electronics', 55000), (2, 'Headphones', 'Electronics', 2500), (3, 'Desk', 'Furniture', 8000),
              (4, 'Chair', 'Furniture', 4500)]),
    'orders': dict(
        ddl=('order_id INT PRIMARY KEY, customer_id INT NOT NULL, order_date DATE NOT NULL, '
             'amount DECIMAL(10,2) NOT NULL, status VARCHAR(12) NOT NULL'),
        cols=['order_id', 'customer_id', 'order_date', 'amount', 'status'],
        rows=[
            (101, 1, '2026-01-03', 57500, 'DELIVERED'),
            (102, 2, '2026-01-09', 8000, 'DELIVERED'),
            (103, 1, '2026-01-21', 4500, 'DELIVERED'),
            (104, 3, '2026-01-28', 2500, 'CANCELLED'),
            (105, 4, '2026-02-02', 12500, 'DELIVERED'),
            (106, 2, '2026-02-14', 2500, 'DELIVERED'),
            (107, 1, '2026-02-25', 8000, 'SHIPPED'),
            (108, 5, '2026-03-04', 55000, 'DELIVERED'),
            (109, 3, '2026-03-10', 4500, 'DELIVERED'),
            (110, 4, '2026-03-18', 2500, 'SHIPPED'),
        ]),
    'order_items': dict(
        ddl='order_id INT, product_id INT, qty INT NOT NULL, PRIMARY KEY (order_id, product_id)',
        cols=['order_id', 'product_id', 'qty'],
        rows=[(101, 1, 1), (101, 2, 1), (102, 3, 1), (103, 4, 1), (104, 2, 1), (105, 3, 1), (105, 4, 1),
              (106, 2, 1), (107, 3, 1), (108, 1, 1), (109, 4, 1), (110, 2, 1)]),
}

def setup(*names):
    sql = ''
    for n in names:
        t = TABLES[n]
        vals = ',\n'.join('(' + ', '.join(_lit(v) for v in r) + ')' for r in t['rows'])
        sql += f'CREATE TABLE {n} ({t["ddl"]});\nINSERT INTO {n} VALUES\n{vals};\n'
    return sql

EMP = setup('departments', 'employees')
SALES = setup('customers', 'products', 'orders', 'order_items')
ALL = EMP + SALES

def _cell(v):
    return '<em>NULL</em>' if v is None else str(v)

def sample(*names, note=None):
    """'Sample Data' card showing the input tables used by the example below it."""
    parts = []
    for n in names:
        t = TABLES[n]
        parts.append(p(f'<strong><code>{n}</code></strong>'))
        hdr = [f'<code>{c}</code>' for c in t['cols']]
        rows = [[_cell(v) for v in r] for r in t['rows']]
        # table() bolds the first column; plain values read fine either way
        parts.append(table(hdr, rows))
    if note:
        parts.append(p(note))
    return card('Sample Data', 'fa-table', *parts)
