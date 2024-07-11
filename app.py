from datetime import datetime, timedelta

from bson import ObjectId
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from pymongo import MongoClient

HOST = "localhost"
PORT = 27017
USERNAME = "admin"
PASSWORD = "forabank"

client = MongoClient(HOST, PORT)
db = client['admin']
reqs = db['requests']
offices = db['work_main_plan']
exceptions = db['work_plan_exceptions']
app = Flask(__name__)
enter_key = False


@app.route('/')
def home_page():
    today = datetime.now().strftime('%Y-%m-%d')
    reqs_lst = reqs.find({"status": "Новый", 'date': {'$gte': today}})
    offices_lst = offices.find()
    offices_lst1 = offices.find()
    return render_template('index.html', requests=reqs_lst, offices=offices_lst, offices1=offices_lst1,
                           enter_key=enter_key)


@app.route('/admin')
def admin_login():
    return render_template('login.html')


@app.route('/check_data', methods=['POST'])
def check_login():
    login = request.form.get('username')
    password = request.form.get('password')
    if login == USERNAME and password == PASSWORD:
        global enter_key
        enter_key = True
    return redirect(url_for('home_page'))


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
    offices_lst = offices.find()
    return render_template('main_work_plan.html', offices=offices_lst)


@app.route('/main_work/office/<office_id>')
def get_office(office_id):
    office = offices.find_one({"_id": ObjectId(office_id)})
    return render_template('office.html', office=office)


@app.route('/main_work/add_office', methods=['POST'])
def add_office():
    office_data = {
        'Office': request.form.get('Office'),
        'work_time': {
            day: {
                'start': request.form.get(f'{day}_start'),
                'end': request.form.get(f'{day}_end'),
                'break': request.form.get(f'{day}_break')
            } for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        }
    }
    offices.insert_one(office_data)
    return redirect(url_for('main_work'))


@app.route('/main_work/update_office/<office_id>', methods=['POST'])
def update_office(office_id):
    office_data = {
        'Office': request.form.get('Office'),
        'work_time': {
            day: {
                'start': request.form.get(f'{day}_start'),
                'end': request.form.get(f'{day}_end'),
                'break': request.form.get(f'{day}_break')
            } for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        }
    }
    print(office_data)
    offices.update_one({'_id': ObjectId(office_id)}, {'$set': office_data})
    return redirect(url_for('main_work'))


@app.route('/main_work/delete_office/<office_id>', methods=['POST'])
def delete_office(office_id):
    offices.delete_one({'_id': ObjectId(office_id)})
    return redirect(url_for('main_work'))


@app.route('/exceptions')
def atypical_work():
    excs = exceptions.find()
    return render_template('exceptions.html', documents=excs)


@app.route('/exceptions/document/<document_id>')
def get_document(document_id):
    document = exceptions.find_one({"_id": ObjectId(document_id)})
    return render_template('document.html', document=document)


@app.route('/exceptions/add_document', methods=['POST'])
def add_document():
    document_data = {
        'office': request.form.get('office'),
        'date': request.form.get('date'),
        'exc': {
            'start_time': request.form.get('start_time'),
            'end_time': request.form.get('end_time')
        }
    }
    exceptions.insert_one(document_data)
    return redirect(url_for('atypical_work'))


@app.route('/exceptions/update_document/<document_id>', methods=['POST'])
def update_document(document_id):
    document_data = {
        'office': request.form.get('office'),
        'date': request.form.get('date'),
        'exc': {
            'start_time': request.form.get('start_time'),
            'end_time': request.form.get('end_time')
        }
    }
    exceptions.update_one({'_id': ObjectId(document_id)}, {'$set': document_data})
    return redirect(url_for('atypical_work'))


@app.route('/exceptions/delete_document/<document_id>', methods=['POST'])
def delete_document(document_id):
    exceptions.delete_one({'_id': ObjectId(document_id)})
    return redirect(url_for('atypical_work'))


if __name__ == '__main__':
    app.run()
