from datetime import datetime

from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient

HOST = "localhost"
PORT = 27017

client = MongoClient(HOST, PORT)
db = client['admin']
reqs = db['requests']
offices = db['work_main_plan']

app = Flask(__name__)


@app.route('/')
def home_page():
    reqs_lst = reqs.find({"status": "Новый"})
    offices_lst = offices.find()
    return render_template('index.html', requests=reqs_lst, offices=offices_lst)


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


@app.route('/get_records/<office_name>/<date>', methods=['GET'])
def get_records(office_name, date):
    curr_reqs = reqs.find({'office': office_name, 'date': date})
    return jsonify([req['time'] for req in curr_reqs])


@app.route('/edit/<req_id>')
def show_update_form(req_id):
    req = reqs.find_one({'_id': ObjectId(req_id)})
    offices_lst = offices.find()
    return render_template('edit.html', req=req, offices=offices_lst)


@app.route('/edit/<req_id>', methods=['POST'])
def update_req(req_id):
    updated_req = {
        'surname': request.form.get('surname'),
        'name': request.form.get('name'),
        'fathername': request.form.get('fathername'),
        'contact_phone': request.form.get('phone_number'),
        'office': request.form.get('office'),
        'date': request.form.get('date'),
        'time': request.form.get('time'),
        'status': request.form.get('status')
    }
    reqs.update_one({'_id': ObjectId(req_id)}, {'$set': updated_req})
    return redirect(url_for('home_page'))


@app.route('/update_status/<req_id>', methods=['POST'])
def update_status(req_id):
    data = request.get_json()
    new_status = data.get('status')
    if new_status:
        reqs.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': new_status}})
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Record not found or status unchanged'}), 404


if __name__ == '__main__':
    app.run()

# Учесть дни календаря (выходные)
# Подредактировать форму изменения записи
# дизайн
# Чекбокс "отражать предыдущие даты"
# Выгрузка в Excel
