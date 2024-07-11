from datetime import datetime, timedelta

from bson import ObjectId
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from pymongo import MongoClient

HOST = "localhost"
PORT = 27017

client = MongoClient(HOST, PORT)
db = client['admin']
reqs = db['requests']
offices = db['work_main_plan']
exceptions = db['work_plan_exceptions']
app = Flask(__name__)


@app.route('/')
def home_page():
    today = datetime.now().strftime('%Y-%m-%d')
    reqs_lst = reqs.find({"status": "Новый", 'date': {'$gte': today}})
    offices_lst = offices.find()
    offices_lst1 = offices.find()
    return render_template('index.html', requests=reqs_lst, offices=offices_lst, offices1=offices_lst1)


@app.template_filter('format_date')
def format_date(value):
    date_obj = datetime.strptime(value, '%Y-%m-%d')
    return date_obj.strftime('%d.%m.%Y')


@app.route('/add', methods=['POST'])
def add_new_request():
    req = {
        "surname": request.form['surname'],
        "name": request.form['name'],
        "fathername": request.form['fathername'],
        "contact_phone": request.form['phone_number'],
        "office": request.form['office'],
        "date": request.form['date'],
        "time": request.form['time'],
        "status": "Новый"
    }

    reqs.insert_one(req)
    return redirect(url_for('home_page'))


@app.route('/get_office_schedule/<office_name>', methods=['GET'])
def get_office_schedule(office_name):
    office = offices.find_one({'Office': office_name})
    if office:
        return jsonify(office['work_time'])
    return jsonify({})


@app.route('/get_exceptions/<office_name>/<selected_date>', methods=['GET'])
def get_exceptions(office_name, selected_date):
    excs = exceptions.find_one({'office': office_name, 'date': selected_date})
    if excs:
        return jsonify(excs['exc'])
    return jsonify({})


@app.route('/get_records/<office_name>/<date>', methods=['GET'])
def get_records(office_name, date):
    curr_reqs = reqs.find({'office': office_name, 'date': date})
    return jsonify([req['time'] for req in curr_reqs])


@app.route('/update_status/<req_id>', methods=['POST'])
def update_status(req_id):
    data = request.get_json()
    new_status = data.get('status')
    if new_status:
        reqs.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': new_status}})
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Record not found or status unchanged'}), 404


@app.route('/export_to_excel', methods=['GET'])
def export_to_excel():
    cursor = reqs.find()
    df = pd.DataFrame(list(cursor))
    file_name = 'all_records.xlsx'
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Записи', index=False)
    writer.close()

    return send_file(file_name, as_attachment=True)


@app.route('/main_work')
def main_work():
    return render_template('main_work_plan.html')


@app.route('/exceptions')
def main_work_plan():
    return render_template('exceptions.html')


if __name__ == '__main__':
    app.run()

# Подредактировать форму изменения записи
# дизайн
# Чекбокс "отражать предыдущие даты"
# Выгрузка в Excel
