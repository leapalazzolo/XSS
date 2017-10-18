#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import threading
import urllib
import argparse
import urlparse
import logging
import urllib2
import httplib
import Queue
import re
import hashlib
import mechanize
from links import links
from bdd import bdd

logging.config.fileConfig('log.ini')
LOGGER = logging.getLogger('root')
LOCK = threading.Lock()
LOCK_BDD = threading.Lock()
#Fuente REGEX: https://github.com/wisec/domxsswiki/wiki/Finding-DOMXSS
RE_DOMXSS_SOURCES = re.compile(r'(location\s*[\[.])|([.\[]\s*["\']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)')
RE_DOMXSS_SINKS = re.compile(r'((src|href|data|location|code|value|action)\s*["\'\]]*\s*\+?\s*=)|((replace|assign|navigate|getResponseHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["\'\]]*\s*\()')
RE_DOMXSS_SINKS_JQUERY = re.compile(r'/after\(|\.append\(|\.before\(|\.html\(|\.prepend\(|\.replaceWith\(|\.wrap\(|\.wrapAll\(|\$\(|\.globalEval\(|\.add\(|jQUery\(|\$\(|\.parseHTML\(/')
COLA_SCRIPTS = Queue.Queue()

def script_analizado_previamente(script):
    u'''
    Devuelve si un script JS fue analizado previamente por pertenecer a una URL
    que fue procesada anteriormente.
    '''
    try:
        encontrado = False
        hasher = hashlib.md5()
        hasher.update(script)
        md5_ = hasher.hexdigest()
        with LOCK:
            if md5_ in COLA_SCRIPTS.queue:
                encontrado = True
            else:
                COLA_SCRIPTS.put(md5_)
    except UnicodeEncodeError:
        LOGGER.debug(u'Error al tratar de revisar si script ya había sido analizado previamente. \n')
    finally:
        return encontrado

class Worker(threading.Thread):
    u'''
    Clase que instanciará los threads encargados de realizar el trabajo
    de buscar las vulnerabilidades XSS.
    '''
    def __init__(self, cola_links, lista_cookies, lista_payloads, db, analisis_reflected, analsis_dom):
        self.cola_links = cola_links
        self.lista_cookies = lista_cookies
        self.lista_payloads = lista_payloads 
        self.analisis_reflected = analisis_reflected
        self.analsis_dom = analsis_dom
        self.db = db
        threading.Thread.__init__(self)
    def run(self):
        u'''
        Busca vulnerabilidades XSS en la URL y sus componenetes mientras haya URLs pendientes.
        '''
        while not self.cola_links.empty():
            vuln_dom, vuln_url, vuln_reflected = None, None, None
            link = self.cola_links.get(timeout=3)
            LOGGER.info(u'Empieza el análisis con la URL: %s\n', link.url)
            if self.analisis_reflected:
                LOGGER.info(u'Empieza el análisis de XSS Reflected en la URL: %s \n', link.url)
                vuln_reflected = buscar_vulnerabilidad_xss(link, self.lista_cookies, self.lista_payloads)
                LOGGER.info(u'Fin del análisis de XSS Reflected en la URL: %s \n', link.url)
                if vuln_reflected:
                    with LOCK_BDD:
                        for k in vuln_reflected:
                            self.db.insertar_vulnerabilidad_reflected(link.url, k, vuln_reflected[k])
            if self.analsis_dom:
                if link.parametros:
                    LOGGER.info(u'Empieza el análisis de parametros en la misma URL: %s \n', link.url)    
                    vuln_url = buscar_vulnerabilidad_xss_en_url(link.url, link.parametros, self.lista_payloads)
                    LOGGER.info(u'Fin del análisis de parámetros de la URL: %s \n', link.url)
                    if vuln_url:
                        with LOCK_BDD:
                            for k in vuln_url:
                                self.db.insertar_vulnerabilidad_reflected_url(link.url, k, vuln_url[k])
                if link.scripts:
                    LOGGER.info(u'Empieza el análsis pasivo DOM Based XSS en la URL: %s \n', link.url)
                    for script in link.scripts:
                        vuln_dom = buscar_vulnerabilidades_dom_xss(script)
                        if vuln_dom:
                            with LOCK_BDD:
                                for linea in vuln_dom:
                                    for valor in vuln_dom[linea]:
                                        self.db.insertar_vulnerabilidad_dom(link.url, valor, script, linea)
                    LOGGER.info(u'Fin del análsis pasivo DOM Based XSS en la URL: %s \n', link.url)
            LOGGER.info(u'Fin del análisis de la URL: %s \n', link.url)
            

def obtener_payloads():
    u'''
    Devuelve la lista de payloads obtenida a través de un archivo payloads.txt
    para facilitar su mantenimiento.
    '''
    lista_payloads = []
    try:
        with open('payloads.txt', 'r') as archivo_payloads:
            for linea in archivo_payloads.read().splitlines():
                lista_payloads.append(linea)
    except IOError as error:
        LOGGER.critical('Error al cargar las payloads: %s', error)
    finally:
        return lista_payloads

def obtener_vulnerabilidades_dom_xss(linea, regex):
    u'''
    Devuelve la lista de vulnerabilidades del tipo DOM Based encontradas
    según la regex pasada (análisis pasivo de SINKS o SOURCES) junto con su posición
    en la línea del script proporcionado.
    '''
    lista_vulnerabilidades = list()
    lista_posiciones = list()
    for patron in regex.finditer(linea, re.MULTILINE):
        for grupo in patron.groups():
            posicion = str(patron.span())
            if grupo is not None and posicion not in lista_posiciones: #Para evitar multiples ocurrencias de la regex sobre lo mismo
                lista_posiciones.append(posicion)
                lista_vulnerabilidades.append(str(grupo))
                LOGGER.debug('Posible vulnerabilidad DOM Based: %s %s.\n', grupo, posicion)
    return lista_vulnerabilidades

def buscar_vulnerabilidades_dom_xss(script):
    u'''
    Devuelve un diccionario con las posibles "vulnerabilidades" DOM Based XSS encontradas en cada script
    a través de una análisis estático con su número de línea, su posición de inicio y la de fin. 
    '''
    dict_dom_xss = dict()
    #for script in scripts:
    if script_analizado_previamente(script):
        LOGGER.debug('Existe un script analizado previamente en otra URL.\n')
        return dict_dom_xss
    nro_linea = 0
    for linea in script.split('\n'):
        nro_linea += 1
        lista_dom_xss = obtener_vulnerabilidades_dom_xss(linea, RE_DOMXSS_SOURCES)
        lista_dom_xss += obtener_vulnerabilidades_dom_xss(linea, RE_DOMXSS_SINKS)
        lista_dom_xss += obtener_vulnerabilidades_dom_xss(linea, RE_DOMXSS_SINKS_JQUERY)
        if lista_dom_xss:
            dict_dom_xss[nro_linea] = lista_dom_xss
            LOGGER.info('Posible vulnerabilidad DOM Based en la URL.\n')
    return dict_dom_xss

def detectar_xss_reflejado(br, payload):
    u'''
    Devuelve si el payload previamente ingresado se encuentra en el HTML de la respuesta.
    '''
    try:
        return payload in br.response().read()
    except httplib.IncompleteRead as error:
        LOGGER.debug('Error al obtener respuesta de la URL. Error: %s', error)
        return False

def buscar_xss_reflejado(br, payload, entrada, form):
    u'''
    Devuelve si existe una vulnerabilidad XSS REFLECTED a partir de encontrar
    el payload previamente ingresado en el HTML de la respuesta.
    '''
    try:
        encontrado = False
        inyectar_payload_en_entrada(br, payload, entrada)
        if detectar_xss_reflejado(br, payload):
            encontrado = True
        br.back()
        br.select_form(nr=form)
        return encontrado
    except mechanize.HTTPError,mechanize.URLError:
        return encontrado

def inyectar_payload_en_entrada(br, payload, entrada):
    '''
    Ingresa un valor a cierto parámetro de entrada de una URL (a partir de su ID o NAME)
    y realiza la petición.
    '''
    try:
        if entrada.has_attr('name'):
            br.form[entrada['name']] = payload
            br.submit()
        else:
            if entrada.has_attr('id'):
                br.form[entrada['id']] = payload
                br.submit()
    except (ValueError, urllib2.URLError, TypeError) as error:
        LOGGER.debug('Error al intentar explotar : %s.\nError: %s.', entrada, error)
        raise error

def buscar_vulnerabilidad_xss_en_url(url_, parametros, lista_payloads):
    u'''
    Por cada uno de los parámetros encontrados en la URL, los empieza a reemplazar de a uno
    por cada una de los payloads. Realiza una petición con la nueva URL y revisa si se
    encuentra en su respuesta el payload ingresado previamente. 
    '''
    br = mechanize.Browser()
    links.configurar_navegador(br)
    parametros_y_payloads = dict()
    url_parseado = list(urlparse.urlparse(url_))
    for indice_parametro, parametro in parametros.items():
        encontrado = False
        for indice_valor, valor in enumerate(parametro):
            p = 0
            while p < len(lista_payloads) and not encontrado:
                payload = lista_payloads[p]
                nuevos_valores = dict(parametros)
                nuevos_valores[indice_parametro][indice_valor] = valor + payload
                url_parseado[4] = urllib.urlencode(nuevos_valores, doseq=True)
                nueva_url = urlparse.urlunparse(url_parseado)
                if links.abrir_url_en_navegador(br, nueva_url):
                    if detectar_xss_reflejado(br, payload):
                        parametros_y_payloads[str(indice_parametro)] = payload
                        encontrado = True
                        LOGGER.info(u'VULNERABLE!!! DOM Based XSS en parámetros URL.\n')
                p += 1
            if encontrado:
                break   #Que la historia me juzgue
    return parametros_y_payloads

def buscar_vulnerabilidad_xss(objeto_link, lista_cookies, lista_payloads):
    '''
    Devuelve las vulnerabilidades encontradas en una URL.
    '''
    br = mechanize.Browser()
    links.configurar_navegador(br)
    if not links.abrir_url_en_navegador(br, objeto_link.url, lista_cookies):
        LOGGER.critical('Error al abrir la URL: %s', objeto_link.url)
        return None
    entrada_y_payload = dict()
    try:
        forms_y_entradas = objeto_link.entradas
        for form in forms_y_entradas:
            br.select_form(nr=form)
            lista_entradas = forms_y_entradas[form]
            for entrada in lista_entradas:
                p = 0
                vulnerable = False
                while p < len(lista_payloads) and not vulnerable:
                    payload = lista_payloads[p]
                    vulnerable = buscar_xss_reflejado(br, payload, entrada, form)
                    p += 1
                    if vulnerable:
                        entrada_y_payload[str(entrada)] = payload
                        LOGGER.info('VULNERABLE!! XSS Reflected:\nEntrada: %s \nPayload: %s', entrada, payload)

    except Exception as error:
        LOGGER.critical(u'Error al procesar URL: %s.\nError: %s\n', objeto_link.url, error)
    finally:
        br.close()
        return entrada_y_payload


        
def main():
    descripcion =   u'''
                    Bienvenido!
                    '''
    epilogo = u'''
              En caso de que no se especifique el tipo de análisis, se hará por defecto
              solamente del tipo XSS Reflected.
              '''
    parser = argparse.ArgumentParser(description=descripcion,
                                     version='1.0',
                                     usage='%(prog)s [options]',
                                     epilog=epilogo)
    parser.add_argument('-c',
                        '--cookies',
                        metavar='Nombre=valor;Nombre=valor',
                        type=str,
                        #nargs='*',
                        help='Las cookies para la URL ingresada.',
                        action='store',
                        dest='cookies'
                        )
    parser.add_argument('-d',
                        '--dom',
                        help=u'Análisis estatico DOM Based XSS de los scripts encontrados en la URL.',
                        action='store_true',
                        dest='dom'
                        )
    parser.add_argument('-r',
                        '--reflected',
                        help=u'Seleccionar un análisis XSS Reflected.',
                        action='store_true',
                        dest='reflected',
                        default=True
                        )
    obligatorios = parser.add_argument_group('required named arguments')
    obligatorios.add_argument('-u',
                              '--url',
                              metavar='http://example.com',
                              type=str,
                              help=u'La URL en la cual se basara el análisis.',
                              action='store',
                              dest='url',
                              required=True
                              )
    
    obligatorios.add_argument('-t',
                              '--threads',
                              metavar='N',
                              type=int,
                              help=u'La cantidad de threads para realizar la búsqueda de vulnerabilidades.',
                              action='store',
                              dest='threads',
                              required=True
                              )
    args = parser.parse_args()
    if not links.es_url_valida(args.url) or links.es_url_prohibida(args.url) or not links.se_puede_acceder_a_url(args.url):
        LOGGER.critical('Revise la URL ingresada.')
        sys.exit(1)
    cookies_validas = None
    if args.cookies:
        cookies_validas = links.obtener_cookies_validas(args.cookies)
        if not cookies_validas:
            LOGGER.critical('Revise las cookies ingresadas.')
            sys.exit(1)
    if args.threads < 1 or args.threads > 15:
        LOGGER.critical('Revise la cantidad de threads ingresada.')
        sys.exit(1)
    lista_payloads = obtener_payloads()
    if not lista_payloads:
        LOGGER.critical('Revise el archivo payloads.txt.')
        sys.exit(1)
    try:
        db = bdd.BDD('bdd/bdd.db', lista_payloads)
    except Exception:
        LOGGER.critical('Error con la BDD.')
        sys.exit(1)
    LOGGER.info('Empieza el programa!\n\n')
    LOGGER.info(u'Empieza la obtención de datos de la URL: %s \n', args.url)
    cola_links = links.obtener_links_validos_desde_url(args.url, cookies_validas)
    LOGGER.info(u'Fin de la obtención de la URL: %s \n', args.url)
    threads = []
    for i in range(args.threads):
        worker = Worker(cola_links, cookies_validas, lista_payloads, db, args.reflected, args.dom)
        threads.append(worker)
        worker.start()
    for t in threads:
        t.join()
    LOGGER.info('\n\nFin el programa!')

if __name__ == '__main__':
    main()    