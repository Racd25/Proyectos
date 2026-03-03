from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

from sqlqueries import QueriesSQLite
from signin.signin import SigninWindow
from admin.admin import AdminWindow

import json
import os
from datetime import datetime, timedelta
import shutil

# Archivos y rutas
ARCHIVO_ESTADO = "estado_variable.json"
ARCHIVO_DB = "pdvDB.sqlite"
CARPETA_RESPALDO = "Respaldo"
RUTA_ESCRITORIO = os.path.join(os.path.expanduser("~"), "Desktop", CARPETA_RESPALDO)

def cargar_estado():
    if not os.path.exists(ARCHIVO_ESTADO):
        estado = {
            "valor": True,
            "fecha_inicio": datetime.now().isoformat(),
            "ultimo_respaldo": None  # Puede ser None si nunca se ha respaldado
        }
        guardar_estado(estado)
        return estado

    with open(ARCHIVO_ESTADO, 'r') as f:
        estado = json.load(f)

        # Convertir fecha_inicio si existe
        if "fecha_inicio" in estado and estado["fecha_inicio"]:
            estado["fecha_inicio"] = datetime.fromisoformat(estado["fecha_inicio"])
        else:
            estado["fecha_inicio"] = datetime.now()  # Valor por defecto si falta

        # Convertir ultimo_respaldo si existe
        if "ultimo_respaldo" in estado and estado["ultimo_respaldo"]:
            estado["ultimo_respaldo"] = datetime.fromisoformat(estado["ultimo_respaldo"])
        else:
            estado["ultimo_respaldo"] = None  # Asegurar que exista

        return estado

def guardar_estado(estado):
    estado_mod = estado.copy()
    # Convertir datetime a string
    if isinstance(estado_mod["fecha_inicio"], datetime):
        estado_mod["fecha_inicio"] = estado["fecha_inicio"].isoformat()
    if isinstance(estado_mod["ultimo_respaldo"], datetime):
        estado_mod["ultimo_respaldo"] = estado["ultimo_respaldo"].isoformat()
    with open(ARCHIVO_ESTADO, 'w') as f:
        json.dump(estado_mod, f, indent=4)

def obtener_valor():
    estado = cargar_estado()
    ahora = datetime.now()
    seis_meses = timedelta(days=180)

    if ahora - estado["fecha_inicio"] >= seis_meses:
        if estado["valor"] is True:
            estado["valor"] = False
            guardar_estado(estado)
        return False
    else:
        return True

def hacer_respaldo():
    """Hace una copia de pdvDB.sqlite en la carpeta local y en el escritorio."""
    # Crear carpeta local si no existe
    if not os.path.exists(CARPETA_RESPALDO):
        os.makedirs(CARPETA_RESPALDO)

    # Crear carpeta en escritorio si no existe
    ruta_escritorio = os.path.join(os.path.expanduser("~"), "Desktop", CARPETA_RESPALDO)
    if not os.path.exists(ruta_escritorio):
        os.makedirs(ruta_escritorio)

    if not os.path.exists(ARCHIVO_DB):
        print(f"⚠️ No se encontró el archivo de base de datos '{ARCHIVO_DB}'. No se puede hacer respaldo.")
        return

    # Nombre del respaldo
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_respaldo = f"pdvDB_respaldo_{timestamp}.sqlite"

    # Rutas destino
    ruta_local = os.path.join(CARPETA_RESPALDO, nombre_respaldo)
    ruta_escritorio = os.path.join(ruta_escritorio, nombre_respaldo)

    try:
        shutil.copy2(ARCHIVO_DB, ruta_local)
        shutil.copy2(ARCHIVO_DB, ruta_escritorio)
        print(f"✅ Respaldo creado en:\n - Carpeta local: {ruta_local}\n - Escritorio: {ruta_escritorio}")
    except Exception as e:
        print(f"❌ Error al hacer respaldo: {e}")

def verificar_y_hacer_respaldo():
    """Verifica si han pasado 7 días desde el último respaldo y, si es así, hace uno nuevo."""
    estado = cargar_estado()
    ahora = datetime.now()
    una_semana = timedelta(days=7)

    ultimo_respaldo = estado.get("ultimo_respaldo")

    if ultimo_respaldo is None or (ahora - ultimo_respaldo) >= una_semana:
        hacer_respaldo()
        estado["ultimo_respaldo"] = ahora
        guardar_estado(estado)
    else:
        print(f"Respaldo no necesario. Último respaldo: {ultimo_respaldo.strftime('%Y-%m-%d %H:%M')}")


class MainWindow(BoxLayout):
    QueriesSQLite.create_tables()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin_widget = AdminWindow()
        self.signin_widget = SigninWindow(self.admin_widget.poner_usuario)
        self.ids.scrn_signin.add_widget(self.signin_widget)
        self.ids.scrn_admin.add_widget(self.admin_widget)


class MainApp(App):
    def build(self):
        # Verificar y hacer respaldo al iniciar
        verificar_y_hacer_respaldo()
        return MainWindow()


if __name__ == "__main__":
    valor_actual = obtener_valor()
    if valor_actual:
        MainApp().run()
    else:
        print("Aplicación bloqueada por haber superado los 6 meses sin activación.")