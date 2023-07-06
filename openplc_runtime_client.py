from pymodbus.client import ModbusTcpClient
from mysql.connector import connect, Error
import sys
import os
import time
import requests
import threading
import json



def timer_function():
    url = 'https://plc-ass-scada-staging-f3c7371fb015.herokuapp.com/process_data'
    client.write_coil(802, 0, id)
    client.write_coil(803, 0, id)
    client.write_coil(804, 0, id)
    prev_value = 1
    while True:
        response = requests.get(url)

        data = response.json()
        value = int(data['value'])
        client.write_coil(801+prev_value, 0, id)
        client.write_coil(801+value, 1, id)
        prev_value = value



def main():
    plc_input_registers = client.read_discrete_inputs(800, 3, id)
    s1 = plc_input_registers.bits[0]
    s2 = plc_input_registers.bits[1]
    s3 = plc_input_registers.bits[2]
    water_level = (s1 + s2 + s3) * 30
    try:
        with connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS'),
            database=os.environ.get('DB_NAME')
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


if __name__ == "__main__":
    client = ModbusTcpClient('127.0.0.1')
    connected = client.connect()
    id = int(input("Please enter the id: "))

    # Create a Timer thread
    timer_thread = threading.Thread(target=timer_function)

    # Start the Timer thread
    timer_thread.start()
    while True:
        main()