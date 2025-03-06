import sqlite3
import pandas as pd
import simplejson

with open('datosDB.json', 'r') as f:
    datos = simplejson.load(f)
print(datos)

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