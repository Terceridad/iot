import os
import paho.mqtt.client as mqtt
import struct
import psycopg2
from datetime import datetime

# Configuración del broker MQTT
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqtt.eclipseprojects.io')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = "pulsus/+/+/metric"

# Configuración de la base de datos TimescaleDB
DB_NAME = os.getenv('DB_NAME', 'healthdb')
DB_USER = os.getenv('DB_USER', 'healthuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'healthpass')
DB_HOST = os.getenv('DB_HOST', 'timescaledb')
DB_PORT = os.getenv('DB_PORT', '5432')

def on_connect(client, userdata, flags, rc):
    print(f"Conectado con código de resultado {rc}")
    client.subscribe(MQTT_TOPIC)

def parse_hex_data(hex_data):
    # Convertir la cadena hexadecimal a bytes
    if hex_data.startswith("0002"):
        data = bytes.fromhex(hex_data[4:])
    else:
        data = bytes.fromhex(hex_data)
    
    # Desempaquetar los datos según la estructura especificada
    company_id = struct.unpack_from('<H', data, 0)[0]
    serial_name = struct.unpack_from('<H', data, 2)[0]
    heart_rate = data[4]
    steps = struct.unpack_from('<I', data, 5)[0] & 0xFFFFFF  # 3 bytes
    blood_press_s = data[8]
    blood_press_d = data[9]
    blood_oxygen = data[10]
    blood_sugar = data[11]
    temperature = struct.unpack_from('<H', data, 12)[0] / 10.0  # Convertir a flotante
    may_tow = data[14]
    may = data[15]
    pressure = data[16]
    calories = struct.unpack_from('<I', data, 17)[0] & 0xFFFFFF  # 3 bytes
    power = data[20]

    return {
        "company_id": company_id,
        "serial_name": serial_name,
        "heart_rate": heart_rate,
        "steps": steps,
        "blood_press_s": blood_press_s,
        "blood_press_d": blood_press_d,
        "blood_oxygen": blood_oxygen,
        "blood_sugar": blood_sugar,
        "temperature": temperature,
        "may_tow": may_tow,
        "may": may,
        "pressure": pressure,
        "calories": calories,
        "power": power
    }

def on_message(client, userdata, msg):
    topic_parts = msg.topic.split('/')
    gateway_id = topic_parts[1]
    device_id = topic_parts[2]
    
    hex_data = msg.payload.decode('utf-8')
    parsed_data = parse_hex_data(hex_data)
    
    # Agregar gateway_id y device_id a los datos parseados
    parsed_data['gateway_id'] = gateway_id
    parsed_data['device_id'] = device_id
    parsed_data['timestamp'] = datetime.now()
    
    insert_into_timescaledb(parsed_data)

def insert_into_timescaledb(data):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        # Asumiendo que tienes una tabla llamada 'health_metrics'
        query = """
        INSERT INTO health_metrics (
            timestamp, gateway_id, device_id, company_id, serial_name, heart_rate,
            steps, blood_press_s, blood_press_d, blood_oxygen, blood_sugar,
            temperature, may_tow, may, pressure, calories, power
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        values = (
            data['timestamp'], data['gateway_id'], data['device_id'],
            data['company_id'], data['serial_name'], data['heart_rate'],
            data['steps'], data['blood_press_s'], data['blood_press_d'],
            data['blood_oxygen'], data['blood_sugar'], data['temperature'],
            data['may_tow'], data['may'], data['pressure'], data['calories'],
            data['power']
        )
        
        cur.execute(query, values)
        conn.commit()
        print("Datos insertados en TimescaleDB")
    except (Exception, psycopg2.Error) as error:
        print("Error al insertar en TimescaleDB:", error)
    finally:
        if conn:
            cur.close()
            conn.close()


def create_table_if_not_exists():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS health_metrics (
        timestamp TIMESTAMPTZ NOT NULL,
        gateway_id TEXT,
        device_id TEXT,
        company_id INTEGER,
        serial_name INTEGER,
        heart_rate SMALLINT,
        steps INTEGER,
        blood_press_s SMALLINT,
        blood_press_d SMALLINT,
        blood_oxygen SMALLINT,
        blood_sugar SMALLINT,
        temperature REAL,
        may_tow SMALLINT,
        may SMALLINT,
        pressure SMALLINT,
        calories INTEGER,
        power SMALLINT
    );
    """)
    cur.execute("SELECT create_hypertable('health_metrics', 'timestamp', if_not_exists => TRUE);")
    conn.commit()
    cur.close()
    conn.close()


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

create_table_if_not_exists()
client.loop_forever()