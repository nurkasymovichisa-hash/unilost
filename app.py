import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'unilost_secret_key_change_me'

# Пароль администратора (по умолчанию admin2026)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin2026')

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------------------------------------
# МУЛЬТИЯЗЫЧНОСТЬ (Словарь переводов)
# -------------------------------------------------------------
TRANSLATIONS = {
    'ky': {
        'title': 'UniLost — Бюро находок',
        'subtitle': 'Университеттеги жоголгон буюмдарды табуунун санариптик экосистемасы',
        'add_item': '➕ Буюм кошуу',
        'search_placeholder': 'Изрөө (мисалы: Студенческий, AirPods)...',
        'all_campuses': 'Бардык корпустар',
        'all_categories': 'Бардык категориялар',
        'admin_login': '🔒 Админка',
        'found': 'Табылды',
        'lost': 'Жоголду',
        'contact': 'Байланыш',
        'telegram': 'Telegram аркылуу жазуу',
        'likes': 'Колдоо',
        'no_items': 'Азырынча кулактандыруулар жок',
        'footer': '© 2026 UniLost. Кампустун санариптик экосистемасы.'
    },
    'ru': {
        'title': 'UniLost — Бюро находок',
        'subtitle': 'Цифровая экосистема поиска утерянных вещей в кампусе',
        'add_item': '➕ Добавить вещь',
        'search_placeholder': 'Поиск (например: Студенческий, AirPods)...',
        'all_campuses': 'Все корпусы',
        'all_categories': 'Все категории',
        'admin_login': '🔒 Админка',
        'found': 'Найдено',
        'lost': 'Потеряно',
        'contact': 'Контакты',
        'telegram': 'Написать в Telegram',
        'likes': 'Поддержать',
        'no_items': 'Объявлений пока нет',
        'footer': '© 2026 UniLost. Цифровая экосистема кампуса.'
    }
}

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            campus TEXT NOT NULL,
            description TEXT NOT NULL,
            contact TEXT NOT NULL,
            telegram TEXT,
            status TEXT NOT NULL,
            image TEXT,
            likes INTEGER DEFAULT 0,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in ['ky', 'ru']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    # Язык по умолчанию — кыргызский
    lang = session.get('lang', 'ky')
    t = TRANSLATIONS[lang]

    search = request.args.get('search', '')
    category = request.args.get('category', '')
    campus = request.args.get('campus', '')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    query = "SELECT * FROM items WHERE (title LIKE ? OR description LIKE ?)"
    params = [f'%{search}%', f'%{search}%']

    if category and category != 'Все' and category != 'Бардыгы':
        query += " AND category = ?"
        params.append(category)

    if campus and campus != 'Все корпусы' and campus != 'Бардык корпустар':
        query += " AND campus = ?"
        params.append(campus)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    items = cursor.fetchall()
    conn.close()

    return render_template('index.html', 
                           items=items, 
                           search=search, 
                           selected_category=category, 
                           selected_campus=campus,
                           t=t,
                           current_lang=lang)

@app.route('/add', methods=['GET', 'POST'])
def add():
    lang = session.get('lang', 'ky')
    t = TRANSLATIONS[lang]
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        campus = request.form['campus']
        description = request.form['description']
        contact = request.form['contact']
        telegram = request.form.get('telegram', '').strip('@')
        status = request.form['status']

        image_filename = ""
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO items (title, category, campus, description, contact, telegram, status, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, category, campus, description, contact, telegram, status, image_filename))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add.html', t=t)

@app.route('/like/<int:item_id>', methods=['POST'])
def like(item_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET likes = likes + 1 WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Туура эмес пароль! / Неверный пароль!'

    if not session.get('is_admin'):
        return render_template('admin_login.html', error=error)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items ORDER BY id DESC")
    items = cursor.fetchall()
    conn.close()
    return render_template('admin.html', items=items)

@app.route('/admin/delete/<int:item_id>', methods=['POST'])
def admin_delete(item_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
