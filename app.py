import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = 'ulyana_nails_secret_key_2026'

DB_NAME = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            duration INTEGER NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            client_phone TEXT NOT NULL,
            service_id INTEGER,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            status TEXT DEFAULT 'Подтверждено',
            FOREIGN KEY (service_id) REFERENCES services(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS schedule_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            is_day_off INTEGER DEFAULT 1
        )
    ''')
    
    c.execute('SELECT COUNT(*) FROM services')
    if c.fetchone()[0] == 0:
        exact_services = [
            ('Маникюр без покрытия', 900, 60),
            ('Маникюр с однотонным покрытием гель-лак', 1900, 90),
            ('Укрепление акригелем', 300, 30),
            ('Снятие чужой работы', 200, 30),
            ('Снятие моей работы без покрытия', 200, 30),
            ('Снятие моей работы с покрытием', 0, 20),
            ('Ремонт одного ногтя', 100, 20),
            ('Наращивание одного ногтя', 200, 30),
            ('Дизайн одного ногтя', 50, 20),
            ('Френч, лунки', 200, 30),
            ('Градиент', 500, 40),
            ('Кошачий глаз, втирка, жемчужный эффект', 200, 20),
            ('Наращивание ногтей (полное)', 2900, 120),
            ('Педикюр: с обработкой стопы без покрытия', 2000, 90),
            ('Педикюр: с обработкой стопы с покрытием гель-лак', 2600, 120),
            ('Педикюр: без обработки стопы (только пальчики) без покрытия', 1300, 60),
            ('Педикюр: без обработки стопы (только пальчики) с покрытием', 2000, 90),
            ('Пилинг ног', 500, 30)
        ]
        c.executemany('INSERT INTO services (name, price, duration) VALUES (?, ?, ?)', exact_services)
    
    conn.commit()
    conn.close()

init_db()

CLIENT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Студия Ульяны Корнильцевой</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #fff5f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .hero { background: linear-gradient(135deg, #212529, #d63384); color: white; padding: 30px 0; margin-bottom: 30px; border-radius: 0 0 25px 25px; }
        .card { border: none; border-radius: 20px; box-shadow: 0 6px 20px rgba(214, 51, 132, 0.1); }
        .btn-primary { background-color: #d63384; border-color: #d63384; }
        .btn-primary:hover { background-color: #b02a6b; border-color: #b02a6b; }
        .logo-img { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 3px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
    </style>
</head>
<body>
    <div class="hero text-center">
        <div class="container">
            <h1 class="fw-bold">Студия Ульяны Корнильцевой</h1>
            <p class="text-white-50 mb-1">г. Екатеринбург, ул. Красных Командиров, 29</p>
            <em class="small text-light">«Сделаю маникюр круче, чем у твоей подруги!»</em>
        </div>
    </div>

    <div class="container mb-5">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card p-4">
                    <h3 class="mb-4 text-center fw-bold text-dark">Онлайн-запись на процедуру</h3>
                    <form method="POST" action="/book">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">1. Выберите услугу (по актуальному прайсу):</label>
                            <select name="service_id" class="form-select form-select-lg" required>
                                {% for s in services %}
                                    <option value="{{ s[0] }}">{{ s[1] }} — {{ s[2] }} ₽ ({{ s[3] }} мин.)</option>
                                {% endfor %}
                            </select>
                        </div>

                        <div class="mb-3">
                            <label class="form-label fw-semibold">2. Выберите дату (прием строго с 12:30 в рабочие дни):</label>
                            <input type="date" name="booking_date" class="form-control form-control-lg" min="{{ min_date }}" required>
                        </div>

                        <div class="mb-3">
                            <label class="form-label fw-semibold">3. Выберите время (доступные окна с 12:30):</label>
                            <select name="booking_time" class="form-select form-select-lg" required>
                                <option value="12:30">12:30</option>
                                <option value="14:00">14:00</option>
                                <option value="15:30">15:30</option>
                                <option value="17:00">17:00</option>
                                <option value="18:30">18:30</option>
                                <option value="20:00">20:00</option>
                            </select>
                            <div class="form-text">Плавающий график мастера с 12:30. Выходные дни заблокированы мастером.</div>
                        </div>

                        <div class="mb-3">
                            <label class="form-label fw-semibold">4. Ваше Имя:</label>
                            <input type="text" name="client_name" class="form-control" placeholder="например, Анна" required>
                        </div>

                        <div class="mb-4">
                            <label class="form-label fw-semibold">5. Ваш номер телефона (для связи):</label>
                            <input type="tel" name="client_phone" class="form-control" placeholder="+7 (999) 000-00-00" required>
                        </div>

                        <button type="submit" class="btn btn-primary btn-lg w-100 py-3 fw-bold">Подтвердить запись</button>
                    </form>
                </div>
                <div class="text-center mt-3">
                    <a href="/admin" class="text-muted text-decoration-none small">Вход для мастера (Админ-панель)</a>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ-панель | Студия Ульяны Корнильцевой</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand mb-0 h1">Кабинет мастера: Студия Ульяны Корнильцевой</span>
            <a href="/logout" class="btn btn-outline-light btn-sm">Выйти</a>
        </div>
    </nav>

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="row mb-5">
            <div class="col-md-12">
                <div class="card shadow-sm p-4">
                    <h4 class="mb-3 fw-bold text-dark">📅 Управление плавающим графиком (Выходные дни)</h4>
                    <p class="text-muted small">Выберите дату, которую хотите сделать выходным днем. На эту дату клиентки записаться не смогут.</p>
                    <form method="POST" action="/admin/block-date" class="row g-3 align-items-center">
                        <div class="col-auto">
                            <input type="date" name="day_off" class="form-control" required>
                        </div>
                        <div class="col-auto">
                            <button type="submit" class="btn btn-danger">Сделать выходным</button>
                        </div>
                    </form>

                    <h6 class="mt-4 fw-semibold">Заблокированные выходные дни:</h6>
                    <ul class="list-group mt-2" style="max-width: 400px;">
                        {% for b in blocked_dates %}
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                {{ b[1] }}
                                <a href="/admin/unblock/{{ b[0] }}" class="btn btn-sm btn-outline-secondary">Удалить выходной</a>
                            </li>
                        {% else %}
                            <li class="list-group-item text-muted">Нет заблокированных дней</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="card shadow-sm p-4">
                    <h4 class="mb-3 fw-bold text-dark">📋 Записи клиентов</h4>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>ID</th>
                                    <th>Имя</th>
                                    <th>Телефон</th>
                                    <th>Услуга</th>
                                    <th>Дата</th>
                                    <th>Время</th>
                                    <th>Статус</th>
                                    <th>Действие</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for b in bookings %}
                                <tr>
                                    <td>{{ b[0] }}</td>
                                    <td class="fw-semibold">{{ b[1] }}</td>
                                    <td>{{ b[2] }}</td>
                                    <td>{{ b[3] }}</td>
                                    <td><span class="badge bg-info text-dark">{{ b[4] }}</span></td>
                                    <td><span class="badge bg-success">{{ b[5] }}</span></td>
                                    <td>{{ b[6] }}</td>
                                    <td>
                                        <a href="/admin/delete/{{ b[0] }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Удалить запись?')">Удалить</a>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="8" class="text-center text-muted py-4">Пока нет ни одной записи</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Вход в админ-панель</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center py-4" style="height: 100vh;">
    <div class="container" style="max-width: 400px;">
        <div class="card shadow p-4">
            <h3 class="text-center mb-4 fw-bold">Вход для Ульяны</h3>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Пароль (по умолчанию 1234):</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-dark w-100 py-2">Войти</button>
            </form>
            <div class="text-center mt-3">
                <a href="/" class="text-muted text-decoration-none small">← На главную к записи</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, price, duration FROM services')
    services = c.fetchall()
    conn.close()
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template_string(CLIENT_TEMPLATE, services=services, min_date=min_date)

@app.route('/book', methods=['POST'])
def book():
    service_id = request.form.get('service_id')
    client_name = request.form.get('client_name')
    client_phone = request.form.get('client_phone')
    booking_date = request.form.get('booking_date')
    booking_time = request.form.get('booking_time')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('SELECT * FROM schedule_blocks WHERE date = ?', (booking_date,))
    if c.fetchone():
        flash('Выбранный день является выходным у мастера. Пожалуйста, выберите другую дату.', 'danger')
        conn.close()
        return redirect(url_for('index'))
    
    c.execute('SELECT * FROM bookings WHERE booking_date = ? AND booking_time = ? AND status = "Подтверждено"', (booking_date, booking_time))
    if c.fetchone():
        flash('К сожалению, это время уже занято. Пожалуйста, выберите другое окошко.', 'warning')
        conn.close()
        return redirect(url_for('index'))
    
    c.execute('''
        INSERT INTO bookings (client_name, client_phone, service_id, booking_date, booking_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (client_name, client_phone, service_id, booking_date, booking_time))
    conn.commit()
    conn.close()
    
    flash(f'Спасибо, {client_name}! Вы успешно записаны на {booking_date} в {booking_time}. Ульяна ждет вас!', 'success')
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '1234':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Неверный пароль', 'danger')
    
    if not session.get('logged_in'):
        return render_template_string(LOGIN_TEMPLATE)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT b.id, b.client_name, b.client_phone, s.name, b.booking_date, b.booking_time, b.status
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        ORDER BY b.booking_date DESC, b.booking_time DESC
    ''')
    bookings = c.fetchall()
    
    c.execute('SELECT id, date FROM schedule_blocks ORDER BY date ASC')
    blocked_dates = c.fetchall()
    conn.close()
    
    return render_template_string(ADMIN_TEMPLATE, bookings=bookings, blocked_dates=blocked_dates)

@app.route('/admin/block-date', methods=['POST'])
def block_date():
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    day_off = request.form.get('day_off')
    if day_off:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO schedule_blocks (date) VALUES (?)', (day_off,))
            conn.commit()
            flash(f'День {day_off} успешно отмечен как выходной.', 'success')
        except sqlite3.IntegrityError:
            flash('Этот день уже заблокирован.', 'warning')
        conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/unblock/<int:id>')
def unblock_date(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM schedule_blocks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Выходной день разблокирован.', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:id>')
def delete_booking(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM bookings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Запись удалена.', 'info')
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
