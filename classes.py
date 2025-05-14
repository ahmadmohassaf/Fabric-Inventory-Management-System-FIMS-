from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3

DB = "fims.db"

class User:
    def __init__(self, user_id, username, password, role, hashed=False):
        self.user_id = user_id
        self.username = username.strip()
        self.password = password if hashed else generate_password_hash(password.strip())
        self.role = role.strip()

    def logIn(self):
        return f"{self.username} has logged in."

    def logOut(self):
        return f"{self.username} has logged out."

    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT rowid, username, password, role FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row:
            user_id, username, password, role = row
            cls_map = {'Admin': Admin, 'InventoryManager': InventoryManager, 'Supplier': Supplier}
            return cls_map.get(role, User)(user_id, username, password, role, hashed=True)
        return None

    def save(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)",
                  (self.username, self.password, self.role))
        conn.commit()
        conn.close()

class Admin(User):
    def __init__(self, user_id, username, password, role, hashed=False):
        super().__init__(user_id, username, password, role, hashed=hashed)

    def CalculateProfit(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT SUM(quantity * price) FROM items")
        result = c.fetchone()[0]
        conn.close()
        return result if result else 0.0

    def ViewItem(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM items")
        items = c.fetchall()
        conn.close()
        return [Item(*row) for row in items]

    def GenerateReport(self):
        income = self.CalculateProfit()
        report = Report(None, datetime.now().strftime("%B"), income, 100, 2000)
        report.save()
        return report

    def CreateAccount(self, new_user):
        new_user.save()
        return f"Account created for {new_user.username}"

class InventoryManager(User):
    def __init__(self, user_id, username, password, role, hashed=False):
        super().__init__(user_id, username, password, role, hashed=hashed)

    def AddItem(self, item):
        item.save()
        return f"Item '{item.name}' added."

    def DeleteItem(self, item_id):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("DELETE FROM items WHERE item_id=?", (item_id,))
        conn.commit()
        conn.close()
        return f"Item ID {item_id} deleted."

    def UpdateItem(self, item):
        item.save()
        return f"Item '{item.name}' updated."

class Supplier(User):
    def __init__(self, user_id, username, password, role, hashed=False):
        super().__init__(user_id, username, password, role, hashed=hashed)

    def OrderFabric(self, item_id, quantity):
        item = Item.get_by_id(item_id)
        if item:
            item.quantity += quantity
            item.save()
            return f"Supplier '{self.username}' ordered {quantity} units of '{item.name}'."
        return "Item not found."

class Item:
    def __init__(self, item_id, name, quantity, category, price):
        self.item_id = item_id
        self.name = name.strip()
        self.quantity = int(quantity)
        self.category = category.strip()
        self.price = float(price)

    def save(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO items (item_id, name, quantity, category, price) VALUES (?, ?, ?, ?, ?)",
                  (self.item_id, self.name, self.quantity, self.category, self.price))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_id(item_id):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM items WHERE item_id=?", (item_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return Item(*row)
        return None

class Report:
    def __init__(self, report_id, month, income, minThreshold, maxThreshold):
        self.report_id = report_id
        self.month = month.strip()
        self.income = float(income)
        self.minThreshold = int(minThreshold)
        self.maxThreshold = int(maxThreshold)

    def checkStockAlert(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM items")
        alerts = []
        for row in c.fetchall():
            item = Item(*row)
            if item.quantity < self.minThreshold:
                alerts.append(f"LOW STOCK: {item.name} ({item.quantity})")
            elif item.quantity > self.maxThreshold:
                alerts.append(f"OVERSTOCK: {item.name} ({item.quantity})")
        conn.close()
        return alerts

    def save(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO reports (month, income, minThreshold, maxThreshold) VALUES (?, ?, ?, ?)",
                  (self.month, self.income, self.minThreshold, self.maxThreshold))
        conn.commit()
        conn.close()

    @staticmethod
    def generate():
        return "Static report generated."
