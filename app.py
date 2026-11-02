from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            contact TEXT NOT NULL,
            status TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM items WHERE (title LIKE ? OR description LIKE ?)"
    params = [f'%{search}%', f'%{search}%']
    
    if category and category != 'Все':
        query += " AND category = ?"
        params.append(category)
        
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    items = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', items=items, search=search, selected_category=category)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        description = request.form['description']
        contact = request.form['contact']
        status = request.form['status']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO items (title, category, description, contact, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, category, description, contact, status))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True)
