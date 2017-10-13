#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sqlite3
import logging
from logging import config

logging.config.fileConfig('log.ini')
LOGGER = logging.getLogger('root')

class BDD(object):
    def __init__(self, ruta_archivo, lista_payload):
        try:
            os.remove(ruta_archivo)
            LOGGER.debug('BDD anterior eliminada.')
        except OSError:
            pass
        conn = sqlite3.connect(ruta_archivo, check_same_thread=False)
        LOGGER.debug('BDD creada!')
        self.conn = conn
        self.archivo = ruta_archivo
        self.cursor = conn.cursor()
        try:
            self.__create_table()
            LOGGER.debug('Tablas creadas en BDD.')
            self.__insertar_en_tabla_xss('1', 'Reflected')
            self.__insertar_en_tabla_xss('2', 'DOM Based')
            self.__insertar_en_tabla_elemento('1', 'Entrada')
            self.__insertar_en_tabla_elemento('2', 'Parametro URL')
            self.__insertar_en_tabla_elemento('3', 'Sink')
            self.__insertar_en_tabla_elemento('4', 'Source')
            for indice, valor in enumerate(lista_payload):
                self.__insertar_en_tabla_payload( indice + 1, valor)
            LOGGER.debug('Datos iniciales cargados en BDD.')
        except sqlite3.Error as error:
            LOGGER.critical('Error al cargar tablas y/o datos.\nError: %s', error)


    def __create_table(self):
        u'''
        Función para crear las tablas y llenar los datos estáticos de las mismas.
        '''
        try:
            self.cursor.execute('CREATE TABLE xss(id INTEGER PRIMARY KEY,tipo TEXT);')
            self.cursor.execute('CREATE TABLE payload(id INTEGER PRIMARY KEY,tipo TEXT);')
            self.cursor.execute('CREATE TABLE elemento(id INTEGER PRIMARY KEY,tipo TEXT);')
            self.cursor.execute('CREATE TABLE posicion(id INTEGER PRIMARY KEY,inicio INTEGER, fin INTEGER, linea TEXT);')
            self.cursor.execute('CREATE TABLE script(id INTEGER PRIMARY KEY,script TEXT);')
            self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al crear tablas.\nError: %s', error)
            raise
        try:
            self.cursor.execute('CREATE TABLE vulnerabilidad(id INTEGER PRIMARY KEY,'\
                                                        'url TEXT,'\
                                                        'xss_id INTEGER,'\
                                                        'elemento_id INTEGER,'\
                                                        'elemento TEXT,'\
                                                        'payload_id INTEGER,'\
                                                        'script_id INTEGER,'\
                                                        'posicion_id INTEGER,'\
                                                        'FOREIGN KEY(xss_id) REFERENCES xss(id),'\
                                                        'FOREIGN KEY(elemento_id) REFERENCES elemento(id),'\
                                                        'FOREIGN KEY(payload_id) REFERENCES payload(id),'\
                                                        'FOREIGN KEY(posicion_id) REFERENCES posicion(id)'\
                                                        'FOREIGN KEY(script_id) REFERENCES script(id)'\
                                                        ');'\
                                )
            self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al crear tabla principal.\nError: %s', error)
            raise
    def __insertar_en_tabla_payload(self, id_, payload):
        try:
            self.cursor.execute("INSERT INTO payload (id, tipo) VALUES (?,?)", (id_, payload,))
            self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al insertar en tabla de payload.\nError: %s', error)
            raise

    def __insertar_en_tabla_xss(self, id_, xss):
        try:
            self.conn.execute("INSERT INTO xss (id, tipo) VALUES (?,?)", (id_, xss,))
            self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al insertar en tabla de xss.\nError: %s', error)
            raise
    
    def __insertar_en_tabla_elemento(self, id_, elemento):
        try:
            self.conn.execute("INSERT INTO elemento (id, tipo) VALUES (?,?)", (id_, elemento,))
            self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al insertar en tabla de elemento.\nError: %s', error)
            raise


if __name__ == '__main__':
    lista = ['"\"><imG/sRc=l oNerrOr=(prompt)() x>",',
             ''"<!--<iMg sRc=--><img src=x oNERror=(prompt)`` x>",'',
             ''"<deTails oNToggle=confi\u0072m()>",'']
    bdd = BDD('bdd.db', lista)