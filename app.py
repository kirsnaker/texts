import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dev-key-123'  # Для разработки

# Функции для работы с JSON-базой
def load_data():
    if not os.path.exists('data.json'):
        return {'users': [], 'posts': []}
    
    with open('data.json', 'r') as f:
        return json.load(f)

def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)

# Инициализация базы данных
def init_db():
    if not os.path.exists('data.json'):
        save_data({'users': [], 'posts': []})

init_db()

# Главная страница
@app.route('/')
def index():
    if 'user_id' in session:
        data = load_data()
        current_user_id = session['user_id']
        
        user_posts = [
            post for post in data['posts']
            if post['author_id'] == current_user_id
        ]
        
        other_posts = [
            post for post in data['posts']
            if post['author_id'] != current_user_id
        ]
        
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
        
        data = load_data()
        
        if any(user['username'] == username for user in data['users']):
            flash('Username already exists')
            return redirect(url_for('register'))
        
        new_user = {
            'id': len(data['users']) + 1,
            'username': username,
            'password': generate_password_hash(password),
            'registered_at': datetime.now().isoformat()
        }
        
        data['users'].append(new_user)
        save_data(data)
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Логин
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        data = load_data()
        user = next((u for u in data['users'] if u['username'] == username), None)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
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
        data = load_data()
        
        new_post = {
            'id': len(data['posts']) + 1,
            'content': content,
            'author_id': session['user_id'],
            'created_at': datetime.now().isoformat()
        }
        
        data['posts'].append(new_post)
        save_data(data)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
