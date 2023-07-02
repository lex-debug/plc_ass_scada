from flask import Flask, render_template, jsonify, json, request, url_for, flash, redirect
from flask_cors import CORS
from werkzeug.exceptions import abort
from mysql.connector import connect, Error
import os
import datetime
from threading import Thread
from pymodbus.client import ModbusTcpClient
from pymodbus.device import ModbusDeviceIdentification
import time
# from scada import factoryioAPI



radio_button_value = 0



app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
app.config['SECRET_KEY'] = '123abc12'
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/graph_list')
def loadLineChartPage():
    return render_template('linechart.html')



@app.route('/data.php')
def get_data():
    # Connect to the MySQL database
    try:
        with connect(
            host=app.config.get('DB_HOST'),
            user=app.config.get('DB_USER'),
            password=app.config.get('DB_PASS'),
            database=app.config.get('DB_NAME')
        ) as connection:
            select_level_query = '''
            SELECT * FROM (SELECT * FROM level ORDER BY dt DESC LIMIT 10)Var1 
            ORDER BY dt ASC
            '''
            # Prepare data for response
            labels = []
            values = []
            labels_tmp = []
            values_tmp = []
            with connection.cursor() as cursor:
                # Fetch data from the database
                cursor.execute(select_level_query)
                result = cursor.fetchall()
                for row in result:
                    labels_tmp.append(row[0].strftime("%Y-%m-%d %H:%M:%S"))   # Assuming the first column is the label
                    values_tmp.append(row[1])
                labels = labels_tmp
                values = values_tmp
                
                labels_tmp = []
                values_tmp = []
    except Error as e:
        print(e)
    
    # Return data as JSON response
    response = {
        'labels': labels,
        'values': values
    }
    json_file = jsonify(response)
    return json_file



@app.route('/get_current_water_level.php')
def get_current_water_level():
    try:
        with connect(
            host=app.config.get('DB_HOST'),
            user=app.config.get("DB_USER"),
            password=app.config.get("DB_PASS"),
            database=app.config.get("DB_NAME")
        ) as connection:
            select_current_water_level_query = 'SELECT level FROM (SELECT * FROM level ORDER BY dt DESC)Var1 LIMIT 1'
            with connection.cursor() as cursor:
                cursor.execute(select_current_water_level_query)
                result = cursor.fetchone()
                final_result = int(float(result[0]))
    except Error as e:
        print(e)
    
    response = {
        'value': str(final_result)
    }
    json_file = jsonify(response)
    return json_file



@app.route('/process_data', methods=('GET', 'POST', ))
def process_data():
    global radio_button_value

    if request.method == 'POST':
        radio_button = request.get_json()
        radio_button_value = radio_button.get("value")

        return "Data processed successfully"
    elif request.method == 'GET':
        response = {
            'value': str(radio_button_value)
        }
        json_file = jsonify(response)
        return json_file
    


if __name__ == '__main__':
    app.run(debug=True)
    
        