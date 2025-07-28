from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime

app = Flask(__name__)

# Конфигурация
DB_FILE = os.path.join(os.path.dirname(__file__), 'database.json')

# Инициализация базы данных
def init_db():
    if not os.path.exists(DB_FILE):
        data = {
            "users": {
                "admin@kirsnake": {
                    "password": generate_password_hash("admin123"),
                    "name": "Admin",
                    "avatar": "A"
                }
            },
            "posts": [
                {
                    "id": 1,
                    "author": "Kirsnake",
                    "avatar": "K",
                    "content": "Добро пожаловать в Kirsnake Texts!",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "likes": 12,
                    "comments": 3,
                    "liked_by": []
                }
            ],
            "comments": [],
            "last_post_id": 1,
            "last_comment_id": 0
        }
        save_db(data)

def load_db():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# API Endpoints
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    db = load_db()
    
    if data['username'] in db['users']:
        return jsonify({"status": "error", "message": "Пользователь уже существует"}), 400
    
    db['users'][data['username']] = {
        "password": generate_password_hash(data['password']),
        "name": data.get('name', data['username']),
        "avatar": data['username'][0].upper()
    }
    save_db(db)
    return jsonify({"status": "success"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    db = load_db()
    
    user = db['users'].get(data['username'])
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({"status": "error", "message": "Неверные данные"}), 401
    
    return jsonify({
        "status": "success",
        "user": {
            "username": data['username'],
            "name": user['name'],
            "avatar": user['avatar']
        }
    })

@app.route('/api/posts', methods=['GET'])
def get_posts():
    db = load_db()
    return jsonify({"posts": db['posts']})

@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    db = load_db()
    
    new_post = {
        "id": db['last_post_id'] + 1,
        "author": data['author'],
        "avatar": data['avatar'],
        "content": data['content'],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "likes": 0,
        "comments": 0,
        "liked_by": []
    }
    
    db['posts'].append(new_post)
    db['last_post_id'] += 1
    save_db(db)
    return jsonify({"post": new_post})

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    data = request.get_json()
    db = load_db()
    
    for post in db['posts']:
        if post['id'] == post_id:
            if data['username'] in post['liked_by']:
                post['liked_by'].remove(data['username'])
                post['likes'] -= 1
            else:
                post['liked_by'].append(data['username'])
                post['likes'] += 1
            save_db(db)
            return jsonify({"likes": post['likes']})
    
    return jsonify({"status": "error"}), 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
