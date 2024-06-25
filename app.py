from flask import Flask, request, render_template, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from io import BytesIO
import locale

app = Flask(__name__)

# Configuración regional para el manejo de números (opcional)
locale.setlocale(locale.LC_ALL, '')  # Ajusta según tu configuración regional

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    cui_input = request.form['cui']
    cui_list = [cui.strip() for cui in cui_input.split(',')]

    data = []
    for cui in cui_list:
        url = f"https://ofi5.mef.gob.pe/ssi/Ssi/Index?codigo={cui}&tipo=2"

        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            with webdriver.Chrome(options=options) as driver:
                driver.get(url)
                time.sleep(6)  # Esperar 6 segundos para que la página cargue

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'td_cu'))
                )

                td_cu = driver.find_element(By.ID, "td_cu").text.strip()
                td_nominv = driver.find_element(By.ID, "td_nominv").text.strip()
                td_mtototal = driver.find_element(By.ID, "td_mtototal").text.strip()

                # Convertir el costo total a número (opcional)
                try:
                    td_mtototal = locale.atof(td_mtototal.replace("S/", "").replace(",", ""))
                except ValueError:
                    td_mtototal = "No se pudo convertir"

                data.append({'CUI': td_cu, 'Nombre de la Inversión': td_nominv, 'Costo Total de la Inversión Actualizado (S/)': td_mtototal})

        except Exception as e:
            print(f"Error al procesar el CUI {cui}: {e}")

    return render_template('index.html', results=data, show_download=True)

@app.route('/download', methods=['POST'])
def download():
    cui_input = request.form['cui']
    cui_list = [cui.strip() for cui in cui_input.split(',')]

    data = []
    for cui in cui_list:
        url = f"https://ofi5.mef.gob.pe/ssi/Ssi/Index?codigo={cui}&tipo=2"
        
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            with webdriver.Chrome(options=options) as driver:
                driver.get(url)
                time.sleep(6)

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'td_cu'))
                )

                td_cu = driver.find_element(By.ID, "td_cu").text.strip()
                td_nominv = driver.find_element(By.ID, "td_nominv").text.strip()
                td_mtototal = driver.find_element(By.ID, "td_mtototal").text.strip()

                # Convertir el costo total a número
                try:
                    td_mtototal = locale.atof(td_mtototal.replace("S/", "").replace(",", ""))
                except ValueError:
                    td_mtototal = "No se pudo convertir"

                # Crear DataFrame para cada CUI
                df = pd.DataFrame({'CUI': [td_cu], 'Nombre de la Inversión': [td_nominv], 
                                'Costo Total de la Inversión Actualizado (S/)': [td_mtototal]})  
                data.append(df) 

        except Exception as e:
            print(f"Error al procesar el CUI {cui}: {e}")

    # Concatenar los DataFrames de cada CUI
    final_df = pd.concat(data, ignore_index=True)

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    final_df.to_excel(writer, index=False, sheet_name='Resultados')
    writer.close()
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="resultados.xlsx")

if __name__ == '__main__':
    app.run(debug=True)