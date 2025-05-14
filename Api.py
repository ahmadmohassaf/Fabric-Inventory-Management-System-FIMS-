from flask import Flask, request, jsonify
from classes import User, Admin, InventoryManager, Supplier, Item, Report
from werkzeug.security import check_password_hash
import sqlite3

app = Flask(__name__)
DB = "fims.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT,
            income REAL,
            minThreshold INTEGER,
            maxThreshold INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    role = data.get("role")
    cls_map = {"Admin": Admin, "InventoryManager": InventoryManager, "Supplier": Supplier}
    user_cls = cls_map.get(role)
    if not user_cls:
        return jsonify({"error": "Invalid role"}), 400

    user = user_cls(None, data["username"], data["password"], role)
    user.save()
    return jsonify({"message": f"{role} account created successfully."}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.get_by_username(data["username"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user and check_password_hash(user.password, data["password"]):
        return jsonify({"message": user.logIn(), "role": user.role}), 200
    return jsonify({"error": "Incorrect password"}), 401

@app.route('/items', methods=['POST'])
def add_item():
    data = request.get_json()
    item = Item(data["item_id"], data["name"], data["quantity"], data["category"], data["price"])
    item.save()
    return jsonify({"message": "Item added."}), 201

@app.route('/items', methods=['GET'])
def get_items():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM items")
    items = [dict(item_id=row[0], name=row[1], quantity=row[2], category=row[3], price=row[4]) for row in c.fetchall()]
    conn.close()
    return jsonify(items), 200

@app.route('/supplier/order', methods=['POST'])
def supplier_order():
    data = request.get_json()
    supplier = User.get_by_username(data["username"])
    if not supplier or not isinstance(supplier, Supplier):
        return jsonify({"error": "Unauthorized supplier"}), 403
    message = supplier.OrderFabric(data["item_id"], data["quantity"])
    return jsonify({"message": message}), 200

@app.route('/admin/report', methods=['POST'])
def admin_report():
    data = request.get_json()
    admin = User.get_by_username(data["username"])
    if not admin or not isinstance(admin, Admin):
        return jsonify({"error": "Unauthorized admin"}), 403
    report = admin.GenerateReport()
    alerts = report.checkStockAlert()
    return jsonify({
        "report": {
            "month": report.month,
            "income": report.income,
            "alerts": alerts
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
