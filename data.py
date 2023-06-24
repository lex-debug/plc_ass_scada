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

# Private function
def upload_water_level():
    global id
    while True: 
        plc_input_registers = client.read_input_registers(100, 3, int(id))
        water_level = float(plc_input_registers.registers[0]) / 10.0
        try:
            with connect(
                host='localhost',
                user=app.config.get('DB_USER'),
                password=app.config.get('DB_PASS'),
                database='plc_ass_scada_db'
            ) as connection:
                insert_level_query = """
                INSERT INTO level
                (level)
                VALUES
                """
                with connection.cursor() as cursor:
                    cursor.execute(insert_level_query+"("+str(water_level)+")")
                    connection.commit()
        except Error as e:
            print(e)
        time.sleep(1)

app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
app.config['SECRET_KEY'] = '123abc12'
CORS(app)

@app.route('/')
def index():
    global dict
    json_dict = json.dumps(dict)
    return render_template('index.html', json_dict=json_dict)



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
        print(id)
        # Turn on the yellow led
        client.write_coil(801, 1, id)

        # For updating the bar
        daqThread = Thread(target=upload_water_level)
        daqThread.start()
    return redirect(url_for('index'))



@app.route('/startDO', methods=('POST', ))
def startSystem():
    global client, id
    
    if request.form['setpoint'] == '':
        flash('Setpoint is required!')
    else:
        dict['setpoint'] = request.form['setpoint']
        sp = int(float(dict['setpoint'])*100)
        # Write to the digital display 1
        client.write_register(104, sp, id)
    return redirect(url_for('index'))



@app.route('/stop_plc', methods=('POST', ))
def stopSystem():
    global client, id

    # Stop everything
    # If want to restart, need to connect again
    client.write_coil(801, 0, id)
    return redirect(url_for('index'))



@app.route('/graph_list')
def loadLineChartPage():
    return render_template('linechart.html')



@app.route('/data.php')
def get_data():
    # Connect to the MySQL database
    try:
        with connect(
            host='localhost',
            user=app.config.get('DB_USER'),
            password=app.config.get('DB_PASS'),
            database='plc_ass_scada_db'
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
    print(app.config.get("DB_USER"))
    print(app.config.get("DB_PASS"))
    try:
        with connect(
            host='localhost',
            user=app.config.get("DB_USER"),
            password=app.config.get("DB_PASS"),
            database='plc_ass_scada_db'
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

if __name__ == '__main__':
    app.run(debug=True)
    
        