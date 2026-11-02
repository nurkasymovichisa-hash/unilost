from datetime import datetime
from flask import Flask, redirect, render_template, request, url_for
import sqlite3

app = Flask(__name__)


# Функция создания базы данных (если её еще нет)
def init_db():
  conn = sqlite3.connect("unilost.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            status_type TEXT,  -- 'lost' (потерял) или 'found' (нашел)
            room TEXT,
            date TEXT
        )
    """)
  conn.commit()
  conn.close()


# Главная страница (список объявлений + поиск)
@app.route("/")
def index():
  conn = sqlite3.connect("unilost.db")
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()

  search = request.args.get("search", "")
  if search:
    cursor.execute(
        "SELECT * FROM items WHERE title LIKE ? OR description LIKE ? ORDER BY"
        " id DESC",
        ("%" + search + "%", "%" + search + "%"),
    )
  else:
    cursor.execute("SELECT * FROM items ORDER BY id DESC")

  items = cursor.fetchall()
  conn.close()
  return render_template("index.html", items=items, search=search)


# Страница добавления объявления
@app.route("/add", methods=["GET", "POST"])
def add_item():
  if request.method == "POST":
    title = request.form["title"]
    description = request.form["description"]
    category = request.form["category"]
    status_type = request.form["status_type"]
    room = request.form["room"]
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect("unilost.db")
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO items (title, description, category, status_type, room, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, description, category, status_type, room, date),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

  return render_template("add.html")


if __name__ == "__main__":
  init_db()
  app.run(debug=True)
