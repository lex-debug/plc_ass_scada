from pymodbus.client import ModbusTcpClient
import time
from mysql.connector import connect, Error
import os
from threading import Thread

class factoryioThread(Thread):
    def __init__(self, ip_addr):
        super().__init__()
        self.ip_addr = ip_addr
        self.slave_id = 1

        self.digital_input_offset = 0
        self.digital_output_offset = 0
        self.register_input_offset = 0
        self.register_output_offset = 0

        self.digital_input_count = 4
        self.digital_output_count = 3
        self.register_input_count = 3
        self.register_output_count = 4

        self.fill_valve_addr = 0
        self.discharge_valve_addr = 1

        self.client = ModbusTcpClient(ip_addr)
        self.connected = self.client.connect()

    def run(self):
        while self.connected:
            self.plc_input = self.client.read_discrete_inputs(self.digital_input_offset, self.digital_input_count, self.slave_id)
            self.factory_io_run_status = self.plc_input.bits[3]

            if self.factory_io_run_status:
                self.start_button = self.plc_input.bits[0]
                self.reset_button = self.plc_input.bits[1]
                self.stop_button = self.plc_input.bits[3]

                self.plc_coil = self.client.read_coils(self.digital_output_offset, self.digital_output_count, self.slave_id)
                self.start_led_status = self.plc_coil.bits[0]
                self.reset_led_status = self.plc_coil.bits[1]
                self.stop_led_status = self.plc_coil.bits[2]

                self.plc_input_register = self.client.read_input_registers(self.register_input_offset, self.register_input_count, self.slave_id)
                self.water_level = float(self.plc_input_register.registers[0] / 100)
                self.discharge_rate = self.plc_input_register.registers[1]
                self.setPoint = self.plc_input_register.registers[2]

                self.plc_holding_register = self.client.read_holding_registers(self.register_output_offset, self.register_output_count, self.slave_id)
                self.fill_valve_voltage = self.plc_holding_register.registers[0]
                self.discharge_valve_voltage = self.plc_holding_register.registers[1]

                try:
                    with connect(
                        host='localhost',
                        user=os.environ.get('DB_USER'),
                        password=os.environ.get('DB_PASS'),
                        database='plc_ass_scada_db'
                    ) as connection:
                        insert_level_query = """
                        INSERT INTO level
                        (level)
                        VALUES
                        """
                        with connection.cursor() as cursor:
                            cursor.execute(insert_level_query+"("+str(self.water_level)+")")
                            connection.commit()
                except Error as e:
                    print(e)
        
                time.sleep(1)
            print('gg')