import sqlite3
from functools import wraps
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from flask import Flask, render_template, request, session, redirect, url_for, flash
import os
import requests
from ml_functions import initialize_models , prepare_features_for_prediction, predict_criticality

users = {
    'admin': 'admin',
    'user': 'user123'
}

matplotlib.use('Agg')

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'secret_key'


def get_absolute_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_db_connection():
    conn = sqlite3.connect(get_absolute_path('databaseP1.db'))
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    resultados = ejecutar_queries_ej2()
    return render_template('metricas_basicas.html', metricas=resultados)

@app.route('/metricas_basicas')
@login_required
def ejercicio2():
    resultados = ejecutar_queries_ej2()
    return render_template('metricas_basicas.html', metricas=resultados)

@app.route('/analisis_fraude')
@login_required
def ejercicio3():
    resultados = ejecutar_queries_ej3()
    return render_template('analisis_fraude.html', resultados=resultados)

@app.route('/visualizaciones')
@login_required
def ejercicio4():
    graficos = ejecutar_queries_ej4()
    return render_template('visualizaciones.html', graphs=graficos)



'''


Ejercicio 2 Práctica 1


'''

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


resultados = ejecutar_queries_ej2()


'''


Ejercicio 3 Practica 1


'''


def ejecutar_queries_ej3():
    con = get_db_connection()
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

    con.close()
    return resultados

'''


EJERCICIO 4 Práctica 1


'''

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

'''


EJERCICIO 1 Práctica 2


'''


@app.route('/top_clientes')
@login_required
def top_clientes():
    x = request.args.get('x', default=8, type=int)
    mostrar_empleados = request.args.get('mostrar_empleados', default='si', type=str) == 'si'

    con = get_db_connection()

    query_clientes = """
        SELECT c.nombre AS cliente, COUNT(t.id_ticket) AS num_incidencias
        FROM tickets_emitidos t
        JOIN clientes c ON t.cliente = c.id_cli
        GROUP BY t.cliente
        ORDER BY num_incidencias DESC
        LIMIT ?;
    """
    top_clientes = pd.read_sql(query_clientes, con, params=(x,)).to_dict('records')

    con.close()

    return render_template('top_clientes.html',
                           top_clientes=top_clientes,
                           mostrar_empleados=mostrar_empleados,
                           top_x=x)


@app.route('/top_tipos_incidencias')
@login_required
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

    return render_template('top_tipos.html',top_tipos=top_tipos,top_x=x)
'''

EJERCICIO 2 Práctica 2


'''



@app.route('/empleados_mas_dedicados')
@login_required
def empleados_mas_dedicados():
    con = get_db_connection()
    query = """
        SELECT 
            e.nombre AS empleado,
            SUM(c.tiempo) AS total_tiempo
        FROM contactos_con_empleados c
        JOIN empleados e ON c.id_emp = e.id_emp
        GROUP BY e.id_emp
        ORDER BY total_tiempo DESC;
    """
    empleados = pd.read_sql(query, con).to_dict('records')
    con.close()

    return render_template('empleados_mas_dedicados.html', empleados=empleados)


'''


EJERCICIO 3 Práctica 2


'''

@app.route('/api')
@login_required
def api():
    url = "https://cve.circl.lu/api/last"
    cves = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for cve in data:
            if 'cveMetadata' in cve:
                cves.append(cve)
            if len(cves) == 10:
                break

    except Exception as e:
        print(f"Error al obtener CVEs: {e}")

    return render_template("api.html", cves=cves)

'''


EJERCICIO 4 Práctica 2


'''

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos')

    return render_template('login.html')

'''

EJERCICIO 5 Práctica 2


'''

@app.route('/prediccion_tickets', methods=['GET', 'POST'])
@login_required
def ejercicio5():
    models_dir = get_absolute_path('models')
    static_dir = get_absolute_path('static')
    os.makedirs(static_dir, exist_ok=True)
        
    models_available = os.path.exists(os.path.join(models_dir, 'logistic_regression.pkl'))
    
    con = get_db_connection()
    clientes = pd.read_sql("SELECT id_cli, nombre FROM clientes", con).to_dict('records')
    tipos_incidentes = pd.read_sql("SELECT id_tipo, nombre FROM tipos_incidentes", con).to_dict('records')
    empleados = pd.read_sql("SELECT id_emp, nombre FROM empleados", con).to_dict('records')
    con.close()
    
    prediction = None
    selected_model = None
    confidence = None
    feature_importance = None
    error_message = None
    ticket_info = None
    prediction_image = None
    
    # POST petition
    if request.method == 'POST':
        try:
            cliente_id = int(request.form['cliente'])
            fecha_apertura = request.form['fecha_apertura']
            fecha_cierre = request.form.get('fecha_cierre', '') # Campo opcional
            es_mantenimiento = 1 if 'es_mantenimiento' in request.form else 0
            tipo_incidencia = int(request.form['tipo_incidencia'])
            selected_model = request.form['modelo']
            
            con = get_db_connection()
            cliente_nombre = pd.read_sql(f"SELECT nombre FROM clientes WHERE id_cli = {cliente_id}", con).iloc[0]['nombre']
            tipo_incidencia_nombre = pd.read_sql(f"SELECT nombre FROM tipos_incidentes WHERE id_tipo = {tipo_incidencia}", con).iloc[0]['nombre']
            con.close()
            
            ticket_info = {
                'cliente_id': cliente_id,
                'cliente_nombre': cliente_nombre,
                'fecha_apertura': fecha_apertura,
                'fecha_cierre': fecha_cierre,
                'es_mantenimiento': 'Sí' if es_mantenimiento == 1 else 'No',
                'tipo_incidencia_id': tipo_incidencia,
                'tipo_incidencia_nombre': tipo_incidencia_nombre
            }
            
            if not models_available:
                models_available = initialize_models(get_absolute_path)               
                
            features = prepare_features_for_prediction(
                cliente_id, fecha_apertura, fecha_cierre, 
                es_mantenimiento, tipo_incidencia,
                get_absolute_path, get_db_connection
            )
            
            model_key = selected_model
            if selected_model == 'linear_regression':
                model_key = 'logistic_regression'
            
            prediction_result = predict_criticality(features, model_key, get_absolute_path)
            
            prediction, confidence, feature_importance = prediction_result
            
            if feature_importance:
                matplotlib.use('Agg')  
                
                plt.figure(figsize=(10, 6))
                feat_names = [item['feature'] for item in feature_importance]
                feat_values = [item['importance'] for item in feature_importance]
                
                sorted_indices = sorted(range(len(feat_values)), key=lambda i: feat_values[i], reverse=True)
                feat_names = [feat_names[i] for i in sorted_indices]
                feat_values = [feat_values[i] for i in sorted_indices]
                
                plt.bar(feat_names, feat_values, color='skyblue')
                plt.title(f'Importancia de características - {selected_model.title()}')
                plt.ylabel('Importancia')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                img_filename = f'{selected_model}_prediction.png'
                img_path = os.path.join(static_dir, img_filename)
                plt.savefig(img_path, dpi=100, bbox_inches='tight')
                plt.close()
                
                prediction_image = img_filename
            
        except Exception as e:
            import traceback
            error_message = f"Error al realizar la predicción: {str(e)}"
            print(f"Error detallado: {traceback.format_exc()}")
    
    return render_template(
        'prediccion_tickets.html',
        clientes=clientes,
        tipos_incidentes=tipos_incidentes,
        empleados=empleados,
        prediction=prediction,
        selected_model=selected_model,
        confidence=confidence,
        feature_importance=feature_importance,
        error_message=error_message,
        models_available=models_available,
        prediction_image=prediction_image,
        ticket_info=ticket_info
    )



if __name__ == '__main__':
    app.run(debug=False)
