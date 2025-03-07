from fastapi import FastAPI, Query
import pandas as pd
from typing import Dict

app = FastAPI()  # Definir la aplicación FastAPI

# Cargar el archivo Excel
file_path = "Concentrado.xlsx"  # Asegúrate de que el archivo esté en la misma carpeta que main.py
xls = pd.ExcelFile(file_path)

# Definir los rangos de columnas para cada categoría con nombres sin espacios
column_ranges = {
    "Lunes": (0, 6),
    "Martes": (0, 6),
    "Miércoles": (0, 6),
    "Jueves": (0, 6),
    "Viernes_quincena": (28, 34),
    "Viernes_no_quincena": (35, 41),
    "Sábado": (7, 13),
    "Domingo": (7, 13),
    "Días_quincena": (14, 20),
    "Días_feriados": (21, 27),
    "Hot_sale": (42, 48)
}

# Diccionario para almacenar los datos estructurados
structured_data = {}

# Cargar los datos en el diccionario
df = pd.read_excel(xls, sheet_name="Hoja 1")

for category, (start_col, end_col) in column_ranges.items():
    category_df = df.iloc[4:, start_col:end_col].copy()
    category_df.columns = ["HORA", "MINUTOS", "NUMERO_TRX", "CLIENTES_UNICOS", "AFECTACION_3", "AFECTACION_40"]
    
    # Convertir datos a formato numérico
    category_df["HORA"] = pd.to_numeric(category_df["HORA"], errors="coerce")
    category_df["MINUTOS"] = pd.to_numeric(category_df["MINUTOS"], errors="coerce")
    category_df["CLIENTES_UNICOS"] = pd.to_numeric(category_df["CLIENTES_UNICOS"], errors="coerce")
    
    # Crear columna de horario en formato HHMM
    category_df["HORARIO"] = category_df["HORA"] * 100 + category_df["MINUTOS"]
    
    # Guardar cada día por separado en structured_data
    structured_data[category] = category_df.dropna().reset_index(drop=True)

@app.get("/")
def root():
    return {"message": "API funcionando correctamente"}

@app.get("/dias-disponibles/")
def obtener_dias_disponibles():
    return {"dias_disponibles": list(structured_data.keys())}

# Función para calcular afectación
def calcular_afectacion(dia: str, hora_inicio: str, hora_fin: str, data: Dict):
    if dia not in data:
        return {"error": "Día no válido. Verifica las opciones disponibles."}
    
    # Convertir horas a formato HHMM
    inicio_hhmm = int(hora_inicio.replace(":", ""))
    fin_hhmm = int(hora_fin.replace(":", ""))
    
    # Filtrar los datos del día específico
    df = data[dia]
    df_filtrado = df[(df["HORARIO"] >= inicio_hhmm) & (df["HORARIO"] <= fin_hhmm)]
    
    if df_filtrado.empty:
        return {"error": "No hay datos para el rango horario seleccionado."}
    
    # Calcular sumas
    total_clientes_unicos = df_filtrado["CLIENTES_UNICOS"].sum()
    afectacion_3 = total_clientes_unicos * 0.03
    afectacion_40 = total_clientes_unicos * 0.40
    
    return {
        "total_clientes_unicos": round(total_clientes_unicos, 2),
        "afectacion_3": round(afectacion_3, 2),
        "afectacion_40": round(afectacion_40, 2)
    }

@app.get("/afectacion/")
def obtener_afectacion(
    dia: str = Query(..., description="Día de la semana (Ej: 'Lunes', 'Martes', etc.)"),
    hora_inicio: str = Query(..., description="Hora de inicio en formato HH:MM"),
    hora_fin: str = Query(..., description="Hora de fin en formato HH:MM")
):
    if dia not in structured_data:
        return {"error": "Día no válido. Verifica las opciones disponibles.", "dias_disponibles": list(structured_data.keys())}

    resultado = calcular_afectacion(dia, hora_inicio, hora_fin, structured_data)
    return resultado