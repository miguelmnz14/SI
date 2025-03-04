import sqlite3
import pandas as pd
import json

f=open('datosDB.json', 'r')
datos=json.load(f)
print(datos)
print(datos["fichajes"])


con = sqlite3.connect('datos.db')
cur = con.cursor()
cur.execute("DROP TABLE tickets_emitidos")
cur.execute ("CREATE TABLE tickets_emitidos ("
    "id_ticket INTEGER,"
	"cliente INTEGER,"
	"fecha_apertura TEXT,"
	"fecha_cierre TEXT,"
	"es_mantenimiento INTEGER,"
	"satisfaccion_cliente INTEGER,"
	"tipo_incidencia INTEGER"
    ");")

cur.execute("DROP TABLE empleados")
cur.execute ("CREATE TABLE empleados ("
	"id_emp INTEGER,"
	"nombre TEXT,"
	"nivel INTEGER,"
	"fecha_contrato TEXT,"
    ");")

cur.execute("DROP TABLE tipos_incidentes")
cur.execute ("CREATE TABLE tipos_incidentes ("
	"id_cli INTEGER,"
	"nombre TEXT,"
    ");")

cur.execute("DROP TABLE contactos_con_empleados")
cur.execute("CREATE TABLE contactos_con_empleados ("
    "id_emp INTEGER,"
    "fecha TEXT,"
    "tiempo NUMERIC,"
    ");")

cur.execute("DROP TABLE clientes")
cur.execute("CREATE TABLE clientes ("
    "id_cli INTEGER,"
    "nombre TEXT,"
    "telefono NUMERIC,"
    "provincia TEXT,"
    ");")

con.commit()

"""
for elem in datos["fichajes"]:
    #print (elem)
    clave= list(elem.keys())[0]
    print(clave)
    print (elem[clave]["nombre"])

    cur.execute("INSERT OR IGNORE INTO fichajes(id,nombre,sucursal,departamento)"\
                "VALUES ('%d','%s', '%s', '%s')" %
                (int(clave), elem[clave]['nombre'], elem[clave]['sucursal'],elem[clave]['departamento']))
    con.commit()
"""
