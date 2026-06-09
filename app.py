from flask import Flask, request, render_template, redirect, url_for, session, send_file
from src.main_logic import AppController
import pandas as pd
import os
import io

app = Flask(__name__)
app.secret_key = 'secret-key-for-session'

controller = AppController()

# Получаем список доступных валют (кэшируем при старте)
try:
    CURRENCY_LIST = sorted(controller.api.get_available_symbols())
except:
    CURRENCY_LIST = ["USD", "EUR", "RUB", "GBP", "JPY", "CHF", "CNY", "CAD", "AUD", "NZD", "INR", "BRL", "ZAR"]

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        success, role = controller.login(username, password)
        if success:
            session['username'] = username
            session['role'] = role
            # Инициализируем значения в сессии, если их нет
            if 'base_currency' not in session:
                session['base_currency'] = 'USD'
                session['target_currencies'] = 'RUB,EUR'
                session['period'] = 7
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Неверные данные. Зарегистрируйтесь, если нет аккаунта.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        success, msg = controller.register(username, password)
        if success:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=msg)
    return render_template('register.html')

@app.route('/logout')
def logout():
    controller.logout()
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_info = controller.get_current_user_info()
    if user_info is None:
        return redirect(url_for('logout'))
    
    # Загружаем из сессии текущие значения (или значения по умолчанию)
    base_currency = session.get('base_currency', 'USD')
    target_currencies = session.get('target_currencies', 'RUB,EUR')
    period = session.get('period', 7)
    
    reports = []
    all_users = []
    selected_user = None
    table_html = None
    message = None
    error = None
    
    if request.method == 'POST' and 'fetch' in request.form:
        # Получаем значения из формы и сохраняем в сессию
        base_currency = request.form['base_currency'].strip().upper()
        target_currencies = request.form['target_currencies'].strip().upper()
        period = int(request.form['period'])
        
        session['base_currency'] = base_currency
        session['target_currencies'] = target_currencies
        session['period'] = period
        
        targets = [t.strip() for t in target_currencies.split(',') if t.strip()]
        if not targets:
            error = 'Укажите хотя бы одну целевую валюту'
        else:
            df = controller.fetch_currency_data(period, base_currency=base_currency, symbols=targets)
            if df is not None:
                session['current_df'] = df.to_json(date_format='iso', orient='split')
                table_html = df.to_html(classes='table table-striped', border=0)
                message = 'Данные загружены'
            else:
                error = 'Не удалось получить данные от API. Проверьте подключение или валюты.'
    
    # Получение списка отчётов (для админа или пользователя)
    if session.get('role') == 'admin' and request.args.get('user'):
        selected_user = request.args.get('user')
        reports = controller.get_reports_for_user(selected_user)
        all_users = controller.get_all_users()
    else:
        reports = controller.list_user_reports()
        if session.get('role') == 'admin':
            all_users = controller.get_all_users()
    
    return render_template('dashboard.html', 
                           user=user_info,
                           table=table_html,
                           message=message,
                           error=error,
                           reports=reports,
                           all_users=all_users,
                           selected_user=selected_user,
                           base_currency=base_currency,
                           target_currencies=target_currencies,
                           period=period,
                           currency_list=CURRENCY_LIST)

@app.route('/download_report/<username>/<filename>')
def download_report(username, filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != username and session.get('role') != 'admin':
        return "Доступ запрещён", 403
    filepath = os.path.join('data/reports', username, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "Файл не найден", 404

@app.route('/delete_report/<username>/<filename>')
def delete_report(username, filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != username and session.get('role') != 'admin':
        return "Доступ запрещён", 403
    controller.delete_report(username, filename)
    return redirect(url_for('dashboard', user=username if session.get('role')=='admin' else None))

@app.route('/save_current_report', methods=['POST'])
def save_current_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'current_df' not in session:
        return redirect(url_for('dashboard'))
    
    try:
        df = pd.read_json(io.StringIO(session['current_df']), orient='split')
    except Exception as e:
        return f"Ошибка чтения данных: {e}", 500
    
    file_format = request.form.get('format', 'excel')
    saved_path = controller.save_report(df, file_format)
    if saved_path:
        return redirect(url_for('dashboard'))
    else:
        return "Ошибка сохранения", 500

if __name__ == '__main__':
    os.makedirs('data/reports', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
