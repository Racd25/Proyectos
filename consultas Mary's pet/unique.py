import sqlite3
import os

# Nombre de la base de datos
db_name = 'pdvDB.sqlite'

# Verificar que existe la base de datos
if not os.path.exists(db_name):
    print(f"Error: La base de datos '{db_name}' no existe.")
    exit()

# Conectar a la base de datos
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

try:
    # 1. Verificar si la tabla actual tiene UNIQUE en 'ci'
    cursor.execute("PRAGMA table_info(consultas)")
    columns = cursor.fetchall()
    ci_column = next((col for col in columns if col[1] == 'ci'), None)
    
    if not ci_column:
        print("Error: La columna 'ci' no existe en la tabla 'consultas'.")
        conn.close()
        exit()

    # Nota: PRAGMA no muestra directamente si hay UNIQUE, pero asumimos que sí

    # 2. Renombrar la tabla actual
    cursor.execute("ALTER TABLE consultas RENAME TO consultas_old")

    # 3. Crear la nueva tabla SIN UNIQUE en 'ci'
    cursor.execute("""
        CREATE TABLE consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_propietario TEXT NOT NULL,
            ci TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            motivo_consulta TEXT,
            nombre_mascota TEXT,
            especie TEXT,
            raza TEXT,
            sexo TEXT,
            edad REAL,
            pelaje TEXT,
            cc TEXT,
            enfermedad TEXT,
            tratamiento TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. Copiar todos los datos de la tabla antigua a la nueva
    cursor.execute("""
        INSERT INTO consultas (
            id, nombre_propietario, ci, telefono, direccion,
            motivo_consulta, nombre_mascota, especie, raza, sexo,
            edad, pelaje, cc, enfermedad, tratamiento, fecha_registro
        )
        SELECT 
            id, nombre_propietario, ci, telefono, direccion,
            motivo_consulta, nombre_mascota, especie, raza, sexo,
            edad, pelaje, cc, enfermedad, tratamiento, fecha_registro
        FROM consultas_old;
    """)

    # 5. Eliminar la tabla antigua
    cursor.execute("DROP TABLE consultas_old")

    # 6. Confirmar cambios
    conn.commit()
    print("✅ Éxito: La restricción UNIQUE en 'ci' ha sido eliminada.")
    print("     La tabla 'consultas' ahora permite valores duplicados en 'ci'.")

except sqlite3.Error as e:
    conn.rollback()
    print(f"❌ Error al modificar la tabla: {e}")
    # Si falla, puedes revertir o restaurar desde backup
finally:
    conn.close()