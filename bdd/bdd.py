#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sqlite3
import logging
import logging.config

logging.config.fileConfig(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'log.ini'))
LOGGER = logging.getLogger('bdd')

TIPO_XSS = ['Reflected', 'DOM Based']
TIPO_ELEMENTO = ['Entrada', 'Parametro URL', 'Sink/Source']

class BDD(object):
    '''
    Objeto que mantendrá la conexión con la BDD. Además, realiza la creación de la misma,
    de sus tablas y la carga inicial de datos.
    '''
    def __init__(self, ruta_archivo, lista_payload):
        try:
            os.remove(ruta_archivo)
            LOGGER.info('BDD anterior eliminada.')
        except OSError:
            pass
        conn = sqlite3.connect(ruta_archivo, check_same_thread=False)
        LOGGER.info('BDD creada!')
        self.conn = conn
        self.archivo = ruta_archivo
        #self.cursor = conn.cursor()
        try:
            self.conn.text_factory = str
            self.__create_table()
            LOGGER.info('Tablas creadas en BDD.')
            for xss in TIPO_XSS:
                self.__insertar_en_tabla_xss(xss)
            for elemento in TIPO_ELEMENTO:
                self.__insertar_en_tabla_elemento(elemento)
            for payload in lista_payload:
                self.__insertar_en_tabla_payload(payload)
            LOGGER.info('Datos iniciales cargados en BDD.')
        except sqlite3.Error as error:
            LOGGER.critical('Error al cargar tablas y/o datos.\nError: %s', error)
            raise


    def __create_table(self):
        u'''
        Función para crear las tablas y llenar los datos estáticos de las mismas.
        '''
        try:
            with self.conn:
                self.conn.execute('CREATE TABLE xss('\
                                                    'id INTEGER PRIMARY KEY AUTOINCREMENT,'\
                                                    'tipo TEXT'\
                                                    ');'
                                 )
                self.conn.execute('CREATE TABLE payload('\
                                                        'id INTEGER PRIMARY KEY AUTOINCREMENT,'\
                                                        'tipo TEXT'\
                                                        ');'
                                 )
                self.conn.execute('CREATE TABLE elemento('\
                                                         'id INTEGER PRIMARY KEY AUTOINCREMENT,'\
                                                         'tipo TEXT'\
                                                         ');'
                                 )
                #self.conn.execute('CREATE TABLE posicion(id INTEGER PRIMARY KEY AUTOINCREMENT,inicio INTEGER, fin INTEGER, linea TEXT);')
                self.conn.execute('CREATE TABLE script('\
                                                       'id INTEGER PRIMARY KEY AUTOINCREMENT,'\
                                                       'script TEXT'\
                                                       ');'
                                 )
                self.conn.execute('CREATE TABLE vulnerabilidad('\
                                                               'id INTEGER PRIMARY KEY AUTOINCREMENT,'\
                                                               'url TEXT,'\
                                                               'xss_id INTEGER,'\
                                                               'elemento_id INTEGER,'\
                                                               'elemento TEXT,'\
                                                               'payload_id INTEGER,'\
                                                               'script_id INTEGER,'\
                                                               #'posicion TEXT,'\
                                                               'linea TEXT,'\
                                                               #'posicion_id INTEGER,'\
                                                               'FOREIGN KEY(xss_id) REFERENCES xss(id),'\
                                                               'FOREIGN KEY(elemento_id) REFERENCES elemento(id),'\
                                                               'FOREIGN KEY(payload_id) REFERENCES payload(id),'\
                                                               #'FOREIGN KEY(posicion_id) REFERENCES posicion(id)'\
                                                               'FOREIGN KEY(script_id) REFERENCES script(id)'\
                                                               ');'
                                   )
                self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al crear tabla principal.\nError: %s', error)
            raise
    def __insertar_en_tabla_payload(self, payload):
        u'''
        Inserta los datos en la tabla 'payload'.
        '''
        try:
            with self.conn:
                self.conn.execute("INSERT INTO payload (tipo) VALUES (?)", (payload,))
                self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al insertar en tabla de payload.\nError: %s', error)
            raise

    def __insertar_en_tabla_xss(self, xss):
        u'''
        Inserta los datos en la tabla 'xss'.
        '''
        try:
            with self.conn:
                self.conn.execute("INSERT INTO xss (tipo) VALUES (?)", (xss,))
                self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al insertar en tabla de xss.\nError: %s', error)
            raise

    def __insertar_en_tabla_elemento(self, elemento):
        u'''
        Inserta los datos en la tabla 'elemento'.
        '''
        try:
            with self.conn:
                self.conn.execute("INSERT INTO elemento (tipo) VALUES (?)", (elemento,))
                self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al insertar en tabla de elemento.\nError: %s', error)
            raise

    def insertar_vulnerabilidad_reflected(self, url, elemento, payload):
        u'''
        Inserta los datos en la tabla 'vulnerabilidad' con su tipo de elemento vulnerable como 'entrada'.
        '''
        self.__insertar_vulnerabilidad_reflected(url, elemento, TIPO_ELEMENTO[0], payload)
    
    def insertar_vulnerabilidad_reflected_url(self, url, elemento, payload):
        u'''
        Inserta los datos en la tabla 'vulnerabilidad' con su tipo de elemento vulnerable como 'parámetro URL'.
        '''
        self.__insertar_vulnerabilidad_reflected(url, elemento, TIPO_ELEMENTO[1], payload)

    def __insertar_vulnerabilidad_reflected(self, url, elemento, tipo_elemento, payload):
        u'''
        Inserta los datos en la tabla 'vulnerabilidad'.
        '''
        try:
            with self.conn:
                self.conn.execute("INSERT INTO vulnerabilidad (url, xss_id, elemento_id, elemento, payload_id)"\
                                  "VALUES( ?, "\
                                          "(SELECT id FROM xss WHERE tipo = ?),"\
                                          "(SELECT id FROM elemento WHERE tipo = ?),"\
                                          "?,"\
                                          "(SELECT id FROM payload WHERE tipo = ?)"\
                                          ")", (url, TIPO_XSS[0], tipo_elemento, elemento, payload,))
                self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al insertar en tabla de vulnerabilidad.\nError: %s', error)
            raise

    def insertar_vulnerabilidad_dom(self, url, elemento, script, linea):
        u'''
        Inserta los datos en la tabla 'vulnerabilidad' con su tipo de xss igual a DOM Based'.
        '''
        try:
            with self.conn:
                cur = self.conn.cursor()
                cur.execute("SELECT id FROM script WHERE script= ?", (script,))
                #resultado = cur.fetchone()
                resultado = cur.fetchone()
                if resultado:
                    script_id = resultado[0]
                else:
                    cur.execute("INSERT OR IGNORE INTO script (script) VALUES (?)", (script,))
                    self.conn.commit()
                    script_id = cur.lastrowid
                cur.execute("INSERT INTO vulnerabilidad (url, xss_id, elemento_id, elemento, script_id, linea)"\
                                  "VALUES( ?, "\
                                          "(SELECT id FROM xss WHERE tipo = ?),"\
                                          "(SELECT id FROM elemento WHERE tipo = ?),"\
                                          "?,"\
                                          "?,"\
                                          "?"\
                                          ")", (url, TIPO_XSS[1], TIPO_ELEMENTO[2], elemento, script_id, linea,))
                self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.debug('Error al insertar en tabla de elemento.\nError: %s', error)
            raise
        finally:
            cur.close()

