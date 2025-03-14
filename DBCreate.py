import sqlite3
import pandas as pd
import simplejson
import matplotlib.pyplot as plt
from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():
    return '<p>Hello, World!</p>'


with open('datosDB.json', 'r', encoding='UTF-8') as f:
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
            (int(ticket["cliente"]), ticket["fecha_apertura"], ticket["fecha_cierre"], es_mantenimiento_val,
             int(ticket["satisfaccion_cliente"]), int(ticket["tipo_incidencia"]))
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

'''


Ejercicio 3


'''


def ejecutar_queries_ej3():
    # 1. Obtener el ID del tipo de incidente "Fraude"
    query = "SELECT id_tipo FROM tipos_incidentes WHERE nombre = 'Fraude';"
    id_fraude = pd.read_sql(query, con).iloc[0]['id_tipo']

    agrupaciones = {
        "empleado": "e.id_emp",
        "nivel_empleado": "e.nivel",
        "cliente": "t.cliente",
        "tipo_incidente": "t.tipo_incidencia",
        "dia_semana": "strftime('%w', t.fecha_apertura)"
    }
    resultados = {}

    for nombre_agrupacion, campo_agrupacion in agrupaciones.items():
        query = f"""SELECT {campo_agrupacion} AS agrupacion,
                COUNT(DISTINCT t.id_ticket) AS num_incidentes,
                COUNT(c.id_ticket) AS num_contactos,
                SUM(c.tiempo) AS total_horas
            FROM tickets_emitidos t
                JOIN contactos_con_empleados c ON t.id_ticket = c.id_ticket
                JOIN empleados e ON c.id_emp = e.id_emp
            WHERE t.tipo_incidencia = {id_fraude} GROUP BY {campo_agrupacion}
        """
        df = pd.read_sql(query, con)

        estadisticas = {
            "media_incidentes": df['num_incidentes'].mean(),
            "mediana_incidentes": df['num_incidentes'].median(),
            "varianza_incidentes": df['num_incidentes'].var(),
            "max_incidentes": df['num_incidentes'].max(),
            "min_incidentes": df['num_incidentes'].min(),
            "media_contactos": df['num_contactos'].mean(),
            "mediana_contactos": df['num_contactos'].median(),
            "varianza_contactos": df['num_contactos'].var(),
            "max_contactos": df['num_contactos'].max(),
            "min_contactos": df['num_contactos'].min(),
            "media_horas": df['total_horas'].mean(),
            "mediana_horas": df['total_horas'].median(),
            "varianza_horas": df['total_horas'].var(),
            "max_horas": df['total_horas'].max(),
            "min_horas": df['total_horas'].min()
        }
        resultados[nombre_agrupacion] = estadisticas

    return resultados


resultados_2 = ejecutar_queries_ej3()

for agrupacion, stats in resultados_2.items():
    print(f"Agrupación: {agrupacion}")
    if isinstance(stats, dict):
        for stat, value in stats.items():
            print(f"\t{stat}: {value}")
    else:
        print(f"\t{stats}")
    print("\n")



def ejecutar_queries_ej4():
    query = """
        SELECT 
            es_mantenimiento,
            AVG((julianday(fecha_cierre) - julianday(fecha_apertura)) * 24) AS media_horas 
        FROM tickets_emitidos
        GROUP BY es_mantenimiento;
    """
    df = pd.read_sql(query, con)

    plt.figure(figsize=(8, 5))
    labels = ['No Mantenimiento', 'Mantenimiento']
    plt.bar(labels, df['media_horas'], color=['red', 'blue'])
    plt.title('Media de tiempo de resolución de incidentes')
    plt.ylabel('Horas')
    plt.xlabel('Tipo de servicio')
    plt.show()

    query = """
        SELECT 
            t.tipo_incidencia,
            (julianday(t.fecha_cierre) - julianday(t.fecha_apertura)) * 24 AS horas_resolucion
        FROM tickets_emitidos t
        WHERE t.fecha_cierre IS NOT NULL;
    """
    df = pd.read_sql(query, con)

    plt.figure(figsize=(10, 6))
    df.boxplot(column='horas_resolucion', by='tipo_incidencia',
               whis=[5, 95],
               patch_artist=True,
               boxprops=dict(facecolor='black'),
               grid=False)
    plt.title('Distribución de tiempos por tipo de incidencia')
    plt.ylabel('Horas de resolución')
    plt.xlabel('Tipo de incidencia')
    plt.xticks(rotation=45)
    plt.show()

    query = """
        SELECT 
            c.nombre AS cliente,
            COUNT(*) AS num_incidentes
        FROM tickets_emitidos t
        JOIN clientes c ON t.cliente = c.id_cli
        WHERE t.es_mantenimiento = 1 AND t.tipo_incidencia != 1
        GROUP BY t.cliente
        ORDER BY num_incidentes DESC
        LIMIT 5;
    """
    df = pd.read_sql(query, con)

    plt.figure(figsize=(10, 6))
    plt.bar(df['cliente'], df['num_incidentes'], color='brown')
    plt.title('Top 5 clientes más críticos')
    plt.ylabel('Número de incidentes')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

    query = """
        SELECT 
            e.nombre AS empleado,
            COUNT(*) AS num_actuaciones
        FROM contactos_con_empleados c
        JOIN empleados e ON c.id_emp = e.id_emp
        GROUP BY c.id_emp
        ORDER BY num_actuaciones DESC;
    """
    df = pd.read_sql(query, con)

    plt.figure(figsize=(12, 6))
    plt.bar(df['empleado'], df['num_actuaciones'], color='purple')
    plt.title('Actuaciones realizadas por empleado')
    plt.ylabel('Número de actuaciones')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    query = """
        SELECT 
            strftime('%w', c.fecha) AS dia_semana,
            COUNT(*) AS num_actuaciones
        FROM contactos_con_empleados c
        GROUP BY dia_semana
        ORDER BY dia_semana;
    """
    df = pd.read_sql(query, con)
    dias_dict = {
        0: 'Lunes',
        1: 'Martes',
        2: 'Miércoles',
        3: 'Jueves',
        4: 'Viernes',
        5: 'Sábado',
        6: 'Domingo'
    }
    df['dia_semana'] = df['dia_semana'].astype(int).map(dias_dict)

    plt.figure(figsize=(10, 6))
    plt.bar(df['dia_semana'], df['num_actuaciones'], color='green')
    plt.title('Actuaciones por día de la semana')
    plt.ylabel('Número de actuaciones')
    plt.xlabel('Día de la semana')
    plt.tight_layout()
    plt.show()


ejecutar_queries_ej4()

if __name__ == '__main__':
    app.run(debug=True)