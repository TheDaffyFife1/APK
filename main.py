import sqlite3
import pandas as pd
from datetime import datetime
import emoji
import mysql.connector
import os
import threading
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
import threading
import subprocess

config_file_path = 'config.txt'

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')

        self.output_label = Label(text="Output will be shown here")
        layout.add_widget(self.output_label)



        btn_python = Button(text="Run Python Script with Root")
        btn_python.bind(on_press=self.run_python_script)
        layout.add_widget(btn_python)

        return layout

    def get_or_prompt_config(self, callback):
        """Lee la configuración de un archivo o la solicita al usuario."""
        config = {}
        if os.path.isfile(config_file_path) and os.path.getsize(config_file_path) > 0:
            print("Leyendo configuración desde el archivo")
            with open(config_file_path, 'r') as file:
                config = {line.split('=')[0]: line.split('=')[1].strip() for line in file if line.strip()}
            callback(config)
        else:
            print("Archivo de configuración no encontrado o vacío. Solicitando configuración al usuario.")
            # Crear un Popup para ingresar la configuración
            content = FloatLayout()
            popup = Popup(title='Configuración Inicial', content=content, size_hint=(0.9, 0.9))

            cliente_input = TextInput(hint_text='Ingrese el nombre del cliente', multiline=False, size_hint=(0.8, 0.1), pos_hint={'x': 0.1, 'y': 0.7})
            estado_input = TextInput(hint_text='Ingrese el nombre del estado', multiline=False, size_hint=(0.8, 0.1), pos_hint={'x': 0.1, 'y': 0.5})
            municipio_input = TextInput(hint_text='Ingrese el nombre del municipio', multiline=False, size_hint=(0.8, 0.1), pos_hint={'x': 0.1, 'y': 0.3})

            def save_config(instance):
                config['cliente'] = cliente_input.text.strip()
                config['estado'] = estado_input.text.strip()
                config['municipio'] = municipio_input.text.strip()
                with open(config_file_path, 'w') as file:
                    for key, value in config.items():
                        file.write(f'{key}={value}\n')
                print("Configuración guardada:", config)
                popup.dismiss()
                callback(config)

            save_button = Button(text='Guardar', size_hint=(0.8, 0.1), pos_hint={'x': 0.1, 'y': 0.1})
            save_button.bind(on_press=save_config)

            content.add_widget(cliente_input)
            content.add_widget(estado_input)
            content.add_widget(municipio_input)
            content.add_widget(save_button)

            popup.open()

    def run_shell_script(self, instance):
        threading.Thread(target=self.run_shell_script_background).start()

    def run_shell_script_background(self):
        output = self.ejecutar_script_shell()
        self.notify_completion("Shell script completed.")
        self.update_output_label(output)

    def run_python_script(self, instance):
        self.get_or_prompt_config(self.run_python_script_background)

    def run_python_script_background(self, config):
        threading.Thread(target=self.run_python_script_task, args=(config,)).start()

    def run_python_script_task(self, config):
        output = self.ejecutar_script_python(config)
        self.notify_completion("Python script completed.")
        self.update_output_label(output)

    def ejecutar_script_shell(self):
        script_path = '/data/data/com.farfay.test/files/script_combinado.sh'
        result = subprocess.run(['sh', script_path], capture_output=True, text=True)
        print(f"Resultado de ejecutar el script de shell: {result.stdout}")
        return result.stdout

    def ejecutar_script_python(self, config):
        # Aquí va tu lógica del script en Python
        # Ejecutar el script de shell con permisos de root
        print("Ejecutando script de shell...")
        output_shell = self.ejecutar_script_shell()
        print(output_shell)

        # Conexión a la base de datos msgstore.db y lectura de datos
        print("Conectando a msgstore.db...")
        con = sqlite3.connect('/sdcard/msgstore.db')
        try:
            chv = pd.read_sql_query("SELECT * from chat_view", con)
        except pd.io.sql.DatabaseError:
            chv = None  # En caso de que el query no devuelva resultados

        usuarios = pd.read_sql_query("SELECT * from 'jid'", con)
        msg = pd.read_sql_query("SELECT * from message", con)
        con.close()

        # Conexión a la base de datos wa.db y lectura de datos
        print("Conectando a wa.db...")
        con1 = sqlite3.connect('/sdcard/wa.db')
        contacts = pd.read_sql_query("SELECT * from wa_contacts", con1)
        contacts['jid'] = contacts['jid'].str.split('@').str[0]

        descriptions = pd.read_sql_query("SELECT * FROM wa_group_descriptions", con1)
        descriptions['jid'] = descriptions['jid'].str.split('@').str[0]

        names = pd.read_sql_query("SELECT * from wa_vnames", con1)
        names['jid'] = names['jid'].str.split('@').str[0]
        con1.close()

        print("Procesando datos...")
        usuarios['user'] = usuarios['user'].astype(str)
        usuarios['user'] = usuarios['user'].str[3:]
        usuarios['server'] = usuarios['server'].apply(lambda x: 'celular' if x.endswith('.net') else ('grupo' if x.endswith('.us') else 'otro'))

        msg = msg.loc[:, ['chat_row_id', 'timestamp', 'received_timestamp', 'text_data', 'from_me']]
        msg = msg.dropna(subset=['text_data'])
        msg['timestamp'] = pd.to_datetime(msg['timestamp'], unit='ms')
        msg['received_timestamp'] = pd.to_datetime(msg['received_timestamp'], unit='ms')

        def mapping(id):
            phone = chv.loc[chv['_id'] == id, 'raw_string_jid'].iloc[0]
            phone = phone.split('@')[0]
            return phone

        def mapping2(id):
            phone2 = usuarios.loc[usuarios['_id'] == id, 'user'].iloc[0]
            return phone2

        def mapping3(id):
            server = usuarios.loc[usuarios['_id'] == id, 'server'].iloc[0]
            return server

        def mapping4(id):
            server = usuarios.loc[usuarios['_id'] == id, 'device'].iloc[0]
            return server

        def mapping5(id):
            name = chv.loc[chv['_id'] == id, 'subject'].iloc[0]
            return name

        msg['number'] = msg['chat_row_id'].apply(lambda x: mapping(x))
        msg['number2'] = msg['chat_row_id'].apply(lambda x: mapping2(x))
        msg = pd.merge(msg, contacts[['jid', 'status']], left_on='number2', right_on='jid', how='left').drop('jid', axis=1)
        msg = pd.merge(msg, names[['jid', 'verified_name']], left_on='number2', right_on='jid', how='left').drop('jid', axis=1)
        msg['server'] = msg['chat_row_id'].apply(lambda x: mapping3(x))
        msg['device'] = msg['chat_row_id'].apply(lambda x: mapping4(x))
        msg['group'] = msg['chat_row_id'].apply(lambda x: mapping5(x))
        msg = pd.merge(msg, descriptions[['jid', 'description']], left_on='number', right_on='jid', how='left').drop('jid', axis=1)

        msg = msg.where(pd.notnull(msg), None)

        def remove_emojis(text):
            if text is None:
                return text
            return emoji.replace_emoji(text, replace='')

        msg['text_data'] = msg['text_data'].apply(remove_emojis)
        msg['description'] = msg['description'].apply(remove_emojis)
        msg['group'] = msg['group'].apply(remove_emojis)
        msg['timestamp'] = pd.to_datetime(msg['timestamp'], format='%m/%d/%Y %I:%M:%S %p')
        msg['cliente'] = config['cliente']
        msg['estado'] = config['estado']
        msg['municipio'] = config['municipio']
        msg['received_timestamp'] = pd.to_datetime(msg['received_timestamp'], format='%m/%d/%Y %I:%M:%S %p')

        csv_file_path = 'messages_processed.csv'
        msg.to_csv(csv_file_path, index=False)

        print("Conectando a MySQL y subiendo datos...")
        MYSQL_USER = "admin"
        MYSQL_PASS = "F@c3b00k"
        MYSQL_HOST = "158.69.26.160"
        MYSQL_DB = "data_wa"

        mysql_con = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB
        )

        cursor = mysql_con.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS extraccion4 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            chat_row_id INT,
            timestamp DATETIME,
            received_timestamp DATETIME,
            text_data TEXT,
            from_me BOOLEAN,
            number VARCHAR(255),
            number2 VARCHAR(255),
            status VARCHAR(255),
            verified_name VARCHAR(255),
            server VARCHAR(255),
            device VARCHAR(255),
            group_name VARCHAR(255),          
            description TEXT,
            cliente VARCHAR(255),
            estado VARCHAR(255),
            municipio VARCHAR(255)
        )
        """)

        add_message = """
        INSERT INTO extraccion4
        (chat_row_id, timestamp, received_timestamp, text_data, from_me, number, number2, status, verified_name, server, device, group_name, description, cliente, estado, municipio) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        msg['timestamp'] = msg['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        msg['received_timestamp'] = msg['received_timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

        data_to_insert = [
            (
                row['chat_row_id'],
                row['timestamp'],
                row['received_timestamp'],
                row['text_data'],
                row['from_me'],
                row['number'],
                row['number2'],
                row['status'],
                row['verified_name'],
                row['server'],
                row['device'],
                row['group'],
                row['description'],
                row['cliente'],
                row['estado'],
                row['municipio']
            ) for index, row in msg.iterrows()
        ]   
        cursor.executemany(add_message, data_to_insert)

        mysql_con.commit()
        cursor.close()
        mysql_con.close()

        print("Datos subidos con éxito a MySQL.")
        return "Tabla creada (si no existía) y datos subidos con éxito."

    def notify_completion(self, message):
        def update_label(dt):
            self.output_label.text += f"\n{message}"
        Clock.schedule_once(update_label)

    def update_output_label(self, output):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', output))

if __name__ == "__main__":
    MyApp().run()
