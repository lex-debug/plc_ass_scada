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

client = None
id = 0
daqThread = None
dict = {'ip_addr_value': '', 'ip_addr_readOnly': False, 'slave_id': '', 'slave_id_readOnly': False, 'setpoint': ''}
connected = False

app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
app.config['SECRET_KEY'] = '123abc12'
CORS(app)



# Private function
def upload_water_level():
    global id
    while True: 
        plc_input_registers = client.read_discrete_inputs(800, 3, id)
        s1 = plc_input_registers.bits[0]
        s2 = plc_input_registers.bits[1]
        s3 = plc_input_registers.bits[2]
        water_level = s1 + s2 + s3
        water_level = water_level * 30
        try:
            with connect(
                host=app.config.get('DB_HOST'),
                user=app.config.get('DB_USER'),
                password=app.config.get('DB_PASS'),
                database=app.config.get('DB_NAME')
            ) as connection:
                insert_level_query = """
                INSERT INTO level_table
                (level)
                VALUES
                """
                with connection.cursor() as cursor:
                    cursor.execute(insert_level_query+"("+str(water_level)+")")
                    connection.commit()
        except Error as e:
            print(e)
        time.sleep(1)



@app.route('/')
def index():
    global dict
    json_dict = json.dumps(dict)
    return render_template('index_local.html', json_dict=json_dict)



@app.route('/connect_server', methods=('POST', ))
def connect_server():
    global client, dict, connected

    dict['ip_addr_value'] = request.form['ip_address']

    if dict['ip_addr_value'] == '':
        flash('IP Address is required!')
    else:
        client = ModbusTcpClient(host=dict['ip_addr_value'])
        connected = client.connect()
        print(connected)

    dict['ip_addr_readOnly'] = connected
    return redirect(url_for('index'))



@app.route('/disconnect_server', methods=('POST', ))
def disconnect_server():
    global client, dict

    dict['ip_addr_value'] = ''
    dict['ip_addr_readOnly'] = False
    dict['slave_id'] = ''
    dict['slave_id_readOnly'] = False
    dict['setpoint'] = ''
    client.close()

    return redirect(url_for('index'))


@app.route('/get_slave_id', methods=('POST', ))
def get_slave_id():
    global client, id, daqThread, dict
    
    if request.form['slave_id'] == '':
        flash('Slave ID is required!')
    else:
        dict['slave_id'] = request.form['slave_id']
        dict['slave_id_readOnly'] = True
        id = int(dict['slave_id'])

         # For updating the bar
        daqThread = Thread(target=upload_water_level)
        daqThread.start()

    return redirect(url_for('index'))



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
            SELECT * FROM (SELECT * FROM level_table ORDER BY dt DESC LIMIT 10)Var1 
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
            select_current_water_level_query = 'SELECT level FROM (SELECT * FROM level_table ORDER BY dt DESC)Var1 LIMIT 1'
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



@app.route('/process_data', methods=['POST'])
def process_data():
    global client, id

    data = request.get_json()
    value = data.get("value")

    client.write_coil(802, 0, id)
    client.write_coil(803, 0, id)
    client.write_coil(804, 0, id)

    client.write_coil(801+value, 1, id)

    return "Data processed successfully"


if __name__ == '__main__':
    app.run(debug=True)