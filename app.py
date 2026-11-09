import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'unilost_secret_key_change_me'

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin2026')
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------------------------------------
# МУЛЬТИЯЗЫЧНОСТЬ
# -------------------------------------------------------------
TRANSLATIONS = {
    'ky': {
        'title': 'UniLost — Бюро находок',
        'subtitle': 'Университеттеги жоголгон буюмдарды табуунун санариптик экосистемасы',
        'add_item': '➕ Буюм кошуу',
        'search_placeholder': 'Изрөө (мисалы: Студенческий, AirPods)...',
        'admin_login': '🔒 Админка',
        'found': 'Табылды',
        'lost': 'Жоголду',
        'contact': 'Байланыш',
        'telegram': 'Telegram аркылуу жазуу',
        'whatsapp': 'WhatsApp аркылуу жазуу',
        'likes': 'Колдоо',
        'comments': 'Пикирлер',
        'write_comment': 'Пикир калтыруу...',
        'send': 'Жөнөтүү',
        'report': 'Жалоба',
        'no_items': 'Азырынча кулактандыруулар жок',
        'footer': '© 2026 UniLost. Кампустун санариптик экосистемасы.'
    },
    'ru': {
        'title': 'UniLost — Бюро находок',
        'subtitle': 'Цифровая экосистема поиска утерянных вещей в кампусе',
        'add_item': '➕ Добавить вещь',
        'search_placeholder': 'Поиск (например: Студенческий, AirPods)...',
        'admin_login': '🔒 Админка',
        'found': 'Найдено',
        'lost': 'Потеряно',
        'contact': 'Контакты',
        'telegram': 'Написать в Telegram',
        'whatsapp': 'Написать в WhatsApp',
        'likes': 'Поддержать',
        'comments': 'Комментарии',
        'write_comment': 'Оставить комментарий...',
        'send': 'Отправить',
        'report': 'Пожаловаться',
        'no_items': 'Объявлений пока нет',
        'footer': '© 2026 UniLost. Цифровая экосистема кампуса.'
    }
}

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Таблица объявлений
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
            reports INTEGER DEFAULT 0,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Таблица комментариев
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            text TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
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
    lang = session.get('lang', 'ky')
    t = TRANSLATIONS[lang]

    search = request.args.get('search', '')
    category = request.args.get('category', '')
    campus = request.args.get('campus', '')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    query = "SELECT * FROM items WHERE (title LIKE ? OR description LIKE ?)"
    params = [f'%{search}%', f'%{search}%']

    if category and category not in ['Все', 'Бардыгы']:
        query += " AND category = ?"
        params.append(category)

    if campus and campus not in ['Все корпусы', 'Бардык корпустар']:
        query += " AND campus = ?"
        params.append(campus)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    items = cursor.fetchall()

    # Загружаем комментарии для всех постов
    items_with_comments = []
    for item in items:
        cursor.execute("SELECT author, text, date FROM comments WHERE item_id = ? ORDER BY id ASC", (item[0],))
        comments = cursor.fetchall()
        items_with_comments.append({
            'data': item,
            'comments': comments
        })

    conn.close()

    return render_template('index.html', 
                           items=items_with_comments, 
                           search=search, 
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

@app.route('/comment/<int:item_id>', methods=['POST'])
def add_comment(item_id):
    author = request.form.get('author', 'Студент').strip() or 'Студент'
    text = request.form.get('text', '').strip()
    if text:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (item_id, author, text) VALUES (?, ?, ?)", (item_id, author, text))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/report/<int:item_id>', methods=['POST'])
def report_item(item_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET reports = reports + 1 WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/like/<int:item_id>', methods=['POST'])
def like(item_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET likes = likes + 1 WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# -------------------------------------------------------------
# РАСШИРЕННАЯ АДМИН-ПАНЕЛЬ С АНАЛИТИКОЙ
# -------------------------------------------------------------
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

    # Сбор аналитики для админа
    cursor.execute("SELECT COUNT(*) FROM items")
    total_items = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM items WHERE status LIKE '%Табылды%' OR status LIKE '%Найдено%'")
    found_items = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM comments")
    total_comments = cursor.fetchone()[0]

    conn.close()

    stats = {
        'total': total_items,
        'found': found_items,
        'comments': total_comments
    }

    return render_template('admin.html', items=items, stats=stats)

@app.route('/admin/toggle_status/<int:item_id>', methods=['POST'])
def admin_toggle_status(item_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM items WHERE id = ?", (item_id,))
    current_status = cursor.fetchone()[0]
    
    new_status = 'Табылды' if 'Жоголду' in current_status or 'Потеряно' in current_status else 'Жоголду'
    cursor.execute("UPDATE items SET status = ? WHERE id = ?", (new_status, item_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:item_id>', methods=['POST'])
def admin_delete(item_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    cursor.execute("DELETE FROM comments WHERE item_id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
