import sqlite3
import pandas as pd
import simplejson

with open('datosDB.json', 'r') as f:
    datos = simplejson.load(f)

def insertar_datos():
    for cliente in datos["clientes"]:
        cur.execute(
            "INSERT INTO clientes (id_cli, nombre, telefono, provincia) VALUES (?, ?, ?, ?)",
            (int(cliente["id_cli"]), cliente["nombre"], cliente["telefono"], cliente["provincia"])
        )

    for tipo in datos["tipos_incidentes"]:
        cur.execute(
            "INSERT INTO tipos_incidentes (id_tipo, nombre) VALUES (?, ?)",
            (int(tipo["id_inci"]), tipo["nombre"])
        )

    for emp in datos["empleados"]:
        cur.execute(
            "INSERT INTO empleados (id_emp, nombre, nivel, fecha_contrato) VALUES (?, ?, ?, ?)",
            (int(emp["id_emp"]), emp["nombre"], int(emp["nivel"]), emp["fecha_contrato"])
        )

    for ticket in datos["tickets_emitidos"]:
        es_mantenimiento_val = 1 if ticket["es_mantenimiento"] else 0
        cur.execute(
            "INSERT INTO tickets_emitidos (cliente, fecha_apertura, fecha_cierre, es_mantenimiento, satisfaccion_cliente, tipo_incidencia) VALUES (?, ?, ?, ?, ?, ?)",
            (int(ticket["cliente"]), ticket["fecha_apertura"], ticket["fecha_cierre"], es_mantenimiento_val, int(ticket["satisfaccion_cliente"]), int(ticket["tipo_incidencia"]))
        )
        ticket_id = cur.lastrowid  

        for contacto in ticket["contactos_con_empleados"]:
            cur.execute(
                "INSERT INTO contactos_con_empleados (id_ticket, id_emp, fecha, tiempo) VALUES (?, ?, ?, ?)",
                (ticket_id, int(contacto["id_emp"]), contacto["fecha"], float(contacto["tiempo"]))
            )

    con.commit()

con = sqlite3.connect('databaseP1.db')
cur = con.cursor()
cur.executescript("""
    DROP TABLE IF EXISTS contactos_con_empleados;
    DROP TABLE IF EXISTS tickets_emitidos;
    DROP TABLE IF EXISTS empleados;
    DROP TABLE IF EXISTS tipos_incidentes;
    DROP TABLE IF EXISTS clientes;

    CREATE TABLE clientes (
        id_cli INTEGER PRIMARY KEY,
        nombre TEXT,
        telefono TEXT,
        provincia TEXT
    );

    CREATE TABLE tipos_incidentes (
        id_tipo INTEGER PRIMARY KEY,
        nombre TEXT
    );

    CREATE TABLE empleados (
        id_emp INTEGER PRIMARY KEY,
        nombre TEXT,
        nivel INTEGER,
        fecha_contrato TEXT
    );

    CREATE TABLE tickets_emitidos (
        id_ticket INTEGER PRIMARY KEY,
        cliente INTEGER,
        fecha_apertura TEXT,
        fecha_cierre TEXT,
        es_mantenimiento INTEGER,
        satisfaccion_cliente INTEGER,
        tipo_incidencia INTEGER,
        FOREIGN KEY(cliente) REFERENCES clientes(id_cli),
        FOREIGN KEY(tipo_incidencia) REFERENCES tipos_incidentes(id_tipo)
    );

    CREATE TABLE contactos_con_empleados (
        id_ticket INTEGER,
        id_emp INTEGER,
        fecha TEXT,
        tiempo REAL,
        FOREIGN KEY(id_ticket) REFERENCES tickets_emitidos(id_ticket),
        FOREIGN KEY(id_emp) REFERENCES empleados(id_emp)
    );
""")


insertar_datos()


'''

EJERCICIO 2

'''
def ejecutar_queries_ej2():
    metricas = {}
    
    # 1. Numero de muestras totales.
    query = "SELECT COUNT(*) AS total FROM tickets_emitidos;"
    metricas['total_muestras'] = pd.read_sql(query, con).iloc[0]['total']
    
    # 2. Media y desviación estándar del total de incidentes en los que ha habido una valoración mayor o igual a 5 por parte del cliente
    query = """SELECT satisfaccion_cliente FROM tickets_emitidos 
               WHERE satisfaccion_cliente >= 5;"""
    df = pd.read_sql(query, con)
    metricas['media_valoracion'] = df['satisfaccion_cliente'].mean()
    metricas['std_valoracion'] = df['satisfaccion_cliente'].std()
    
    # 3. Media y desviación estándar del total del número de incidentes por cliente.
    query = """SELECT cliente, COUNT(*) AS num_incidentes 
               FROM tickets_emitidos GROUP BY cliente;"""
    df = pd.read_sql(query, con)
    metricas['media_incidentes_cliente'] = df['num_incidentes'].mean()
    metricas['std_incidentes_cliente'] = df['num_incidentes'].std()
    
    # 4. Media y desviación estándar del número de horas totales realizadas en cada incidente.
    query = """SELECT id_ticket, SUM(tiempo) AS total_horas 
               FROM contactos_con_empleados GROUP BY id_ticket;"""
    df = pd.read_sql(query, con)
    metricas['media_horas_incidente'] = df['total_horas'].mean()
    metricas['std_horas_incidente'] = df['total_horas'].std()
    
    # 5. Valor mínimo y valor máximo del total de horas realizadas por los empleados.
    query = """SELECT id_emp, SUM(tiempo) AS total_horas 
               FROM contactos_con_empleados GROUP BY id_emp;"""
    df = pd.read_sql(query, con)
    metricas['min_horas_empleado'] = df['total_horas'].min()
    metricas['max_horas_empleado'] = df['total_horas'].max()
    
    # 6. Valor mínimo y valor máximo del )empo entre apertura y cierre de incidente.
    query = """SELECT id_ticket, 
               (julianday(fecha_cierre) - julianday(fecha_apertura)) * 24 AS horas 
               FROM tickets_emitidos WHERE fecha_cierre IS NOT NULL;"""
    df = pd.read_sql(query, con)
    metricas['min_tiempo_cierre'] = df['horas'].min()
    metricas['max_tiempo_cierre'] = df['horas'].max()
    
    # 7. Valor mínimo y valor máximo del número de incidentes atendidos por cada empleado
    query = """SELECT id_emp, COUNT(DISTINCT id_ticket) AS total 
               FROM contactos_con_empleados GROUP BY id_emp;"""
    df = pd.read_sql(query, con)
    metricas['min_incidentes_empleado'] = df['total'].min()
    metricas['max_incidentes_empleado'] = df['total'].max()
    
    return metricas

resultados = ejecutar_queries_ej2()
for sentencia, result in resultados.items():
    print(f"{sentencia}: {result}")

