import sqlite3
import pandas as pd
import simplejson
import matplotlib.pyplot as plt
import matplotlib
from flask import Flask, render_template, request
import os

matplotlib.use('Agg')

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

def get_absolute_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_db_connection():
    conn = sqlite3.connect(get_absolute_path('databaseP1.db'))
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    resultados = ejecutar_queries_ej2()
    return render_template(get_absolute_path('templates/ejercicio2.html'), metricas=resultados)

@app.route('/ejercicio2')
def ejercicio2():
    resultados = ejecutar_queries_ej2()
    return render_template(get_absolute_path('templates/ejercicio2.html'), metricas=resultados)

@app.route('/ejercicio3')
def ejercicio3():
    resultados = ejecutar_queries_ej3()
    return render_template(get_absolute_path('templates/ejercicio3.html'), resultados=resultados)

@app.route('/ejercicio4')
def ejercicio4():
    graficos = ejecutar_queries_ej4()
    return render_template(get_absolute_path('templates/ejercicio4.html'), graphs=graficos)

@app.route('/top_clientes')
def top_clientes():
    x = request.args.get('x', default=8, type=int)
    con = get_db_connection()
    query = """
        SELECT c.nombre AS cliente, COUNT(t.id_ticket) AS num_incidencias
        FROM tickets_emitidos t
        JOIN clientes c ON t.cliente = c.id_cli
        GROUP BY t.cliente
        ORDER BY num_incidencias DESC
        LIMIT ?;
    """
    top_clientes = pd.read_sql(query, con, params=(x,)).to_dict('records')
    con.close()

    return render_template(get_absolute_path('templates/top_clientes.html'), top_clientes=top_clientes, top_x=x)

@app.route('/top_tipos_incidencias')
def top_tipos_incidencias():
    x = request.args.get('x', default=5, type=int)
    con = get_db_connection()
    query = """
        SELECT ti.nombre AS tipo_incidencia, 
               SUM(ce.tiempo) AS tiempo_total_resolucion
        FROM tickets_emitidos t
        JOIN tipos_incidentes ti ON t.tipo_incidencia = ti.id_tipo
        JOIN contactos_con_empleados ce ON t.id_ticket = ce.id_ticket
        GROUP BY t.tipo_incidencia
        ORDER BY tiempo_total_resolucion DESC
        LIMIT ?;
    """
    top_tipos = pd.read_sql(query, con, params=(x,)).to_dict('records')
    con.close()

    return render_template(get_absolute_path('templates/top_tipos.html'), top_tipos=top_tipos, top_x=x)

def ejecutar_queries_ej2():
    con = get_db_connection()
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

    # 6. Valor mínimo y valor máximo del tiempo entre apertura y cierre de incidente.
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

    con.close()
    return metricas

def ejecutar_queries_ej4():
    con = get_db_connection()

    # 1: Media de tiempo de resolución
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
    plt.savefig(get_absolute_path('static/grafico1.png'), bbox_inches='tight')
    plt.close()

    # 2: Bigotes por tipo de incidencia
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
    plt.savefig(get_absolute_path('static/grafico2.png'), bbox_inches='tight')
    plt.close()

    # 3: Top 5 clientes críticos
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
    plt.savefig(get_absolute_path('static/grafico3.png'), bbox_inches='tight')
    plt.close()

    # 4: Actuaciones por empleado
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
    plt.savefig(get_absolute_path('static/grafico4.png'), bbox_inches='tight')
    plt.close()

    # 5: Actuaciones por día
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
    plt.savefig(get_absolute_path('static/grafico5.png'), bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    app.run(debug=False)