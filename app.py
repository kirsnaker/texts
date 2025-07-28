from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dev-key-123'  # Для разработки

# Инициализация БД
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        author_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Главная страница
@app.route('/')
def index():
    if 'user_id' in session:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Получаем посты пользователя
        cursor.execute('''
        SELECT p.id, p.content, p.created_at 
        FROM posts p
        WHERE p.author_id = ?
        ORDER BY p.created_at DESC
        ''', (session['user_id'],))
        user_posts = cursor.fetchall()
        
        # Получаем посты других пользователей
        cursor.execute('''
        SELECT p.id, p.content, u.username, p.created_at 
        FROM posts p
        JOIN users u ON p.author_id = u.id
        WHERE p.author_id != ?
        ORDER BY p.created_at DESC
        ''', (session['user_id'],))
        other_posts = cursor.fetchall()
        
        conn.close()
        
        return render_template('index.html',
                             username=session['username'],
                             user_posts=user_posts,
                             other_posts=other_posts)
    return redirect(url_for('login'))

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if len(username) < 3 or len(password) < 4:
            flash('Username must be at least 3 characters and password 4 characters')
            return redirect(url_for('register'))
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO users (username, password)
            VALUES (?, ?)
            ''', (username, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists')
            return redirect(url_for('register'))
        finally:
            conn.close()
    
    return render_template('register.html')

# Логин
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, username, password FROM users WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
        return redirect(url_for('login'))
    
    return render_template('login.html')

# Выход
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

# Добавление поста
@app.route('/post', methods=['POST'])
def add_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form['content'].strip()
    if len(content) > 0:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO posts (content, author_id)
        VALUES (?, ?)
        ''', (content, session['user_id']))
        conn.commit()
        conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
