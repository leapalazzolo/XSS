#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import httplib
import urllib2
import logging
import logging.config
import urlparse
import Queue
import mechanize
from bs4 import BeautifulSoup

logging.config.fileConfig(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'log.ini'))
LOGGER = logging.getLogger('links')
REGEX_ARCHIVO, REGEX_CARPETA, REGEX_DOMINIO_O_SUBDOMINIO = None, None, None
BLACKLIST = ['.png', '.jpg', '.jpeg', '.mp3', '.mp4', '.gif', '.svg',
             '.pdf', '.doc', '.docx', '.zip', '.rar', '.rss', '.js', '.min.js']

class Links(object):
    u'''
    Clase que posee todos la información necesaria para
    analizar la existencia de una vulnerabilidad XSS sobre
    una URL.
    '''
    def __init__(self, url_):
        self._url = url_
        self._scripts = list()
        self._entradas = dict()
        self._html = str()
        self._parametros_url = dict()

    @property
    def url(self):
        return self._url

    @property
    def scripts(self):
        return self._scripts

    @scripts.setter
    def scripts(self, script):
        self._scripts = script

    @property
    def html(self):
        return self._html

    @html.setter
    def html(self, html):
        self._html = html

    @property
    def entradas(self):
        return self._entradas

    @entradas.setter
    def entradas(self, entradas):
        self._entradas = entradas

    @property
    def parametros(self):
        return self._parametros_url

    @parametros.setter
    def parametros(self, parametros_url):
        self._parametros_url = parametros_url

def _compilar_regex(regex_link_a_archivo, regex_link_a_carpeta, regex_dominio_o_subdominio):
    u'''
    Compila las regex.
    '''
    global REGEX_ARCHIVO, REGEX_CARPETA, REGEX_DOMINIO_O_SUBDOMINIO
    REGEX_ARCHIVO = re.compile(regex_link_a_archivo)
    REGEX_CARPETA = re.compile(regex_link_a_carpeta)
    REGEX_DOMINIO_O_SUBDOMINIO = re.compile(regex_dominio_o_subdominio)

def obtener_parametros_de_la_url(url_):
    '''
    Devuelve los parametros encontrados en la query de una URL.
    '''
    url_parseado = urlparse.urlsplit(url_)
    return urlparse.parse_qs(url_parseado.query) #allow_fragments=False,keep_blank_values=True)

def obtener_scripts_desde_url(url_, esquema, html):
    '''
    Devuelve los scripts encontrados en la url, ya sean los que estan presentes
    en el mismo html o los que son referenciados a traves de un archivo que pertenece
    al dominio o un subdominio.
    '''
    html_parseado = BeautifulSoup(html, 'html.parser')
    scripts = set()
    for script in html_parseado.findAll('script'):
        texto = script.getText()
        if texto != '':
            scripts.add(texto)
            LOGGER.info('Script encontrado en el html de la url %s', url_)
        else:
            if script.has_attr('src'):
                link_script = obtener_link_valido(url_, script['src'], esquema)
                if link_script is not None:
                    try:
                        script_js = urllib2.urlopen(link_script).read()
                        scripts.add(script_js)
                        LOGGER.info('Script externo encontrado en referencia de la url %s', url_)
                    except (urllib2.HTTPError, ValueError) as error:
                        LOGGER.info('Error al procesar script en la url %s. Error: %s', url_, error)
    return list(scripts)

def obtener_link_valido(url_, link, esquema):
    u'''
    Devuelve el link en formato URL en caso de que pertenezca a la misma
    o a un subdominio.
    '''
    link_valido = None
    if REGEX_ARCHIVO.match(link) is not None or REGEX_CARPETA.match(link) is not None:
        link_valido = urlparse.urljoin(url_, link)
        LOGGER.info('Link %s encontrado perteneciente a la url %s', link_valido, url_)
    else:
        if REGEX_DOMINIO_O_SUBDOMINIO.match(link) is not None and link != '/':
            link_valido = link
            if link_valido[0] == '/' and link_valido[1] == '/':
                link_valido = link_valido.replace('//', esquema + '://')
            if '#' in link_valido:
                link_valido = link_valido[:link_valido.index('#')]
                LOGGER.info('Link %s encontrado perteneciente a subdominio de la url %s', link_valido, url_)
    return link_valido

def obtener_entradas_desde_url(html):
    '''
    Devuelve los 'inputs' encontrados en los 'form' del html que son posibles de
    ingresar texto y explotar una vulnerabilidad XSS.
    '''
    nro_form = 0
    forms_y_parametros = dict()
    html_parseado = BeautifulSoup(html, 'html.parser')
    listform = ['text', 'password', 'email', 'url', 'search']
    for form in html_parseado.findAll('form'):
        lista_parametros = form.findAll('input', {'type':''})
        lista_parametros += form.findAll('input', {'type':listform})
        lista_parametros += form.findAll('textarea')
        if lista_parametros:
            forms_y_parametros[nro_form] = lista_parametros
        nro_form += 1
    return forms_y_parametros

def configurar_navegador(browser):
    '''
    Configura las caracteristicas necesarias para el navegador proporcionado
    por Mechanize.
    '''
    browser.addheaders = [('User-agent',
                           'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127 Firefox/2.0.0.11')]
    browser.set_handle_robots(False)
    browser.set_handle_refresh(False)

def es_url_prohibida(url_):
    '''
    Devuelve si una URL es un archivo el cual no es
    necesario/posible inyectar un payload XSS.
    '''

    for extension in BLACKLIST:
        if extension in url_[-len(extension):]:
            LOGGER.info('URL %s con extension prohibida:  %s', url_, extension)
            return True
    return False


def es_url_valida(url_):
    """Devuelve si una url se encuentra bien formada y existe conexion hacia ella.

    >>>es_url_valida('python.org')
    False

    >>>es_url_valida('https://www.python.org')
    True
    """
    url_parseado = urlparse.urlparse(url_)
    return all([url_parseado.scheme, url_parseado.netloc])

def se_puede_acceder_a_url(url_):
    """Devuelve si en una url existe conexion hacia ella.

    >>>se_puede_acceder_a_url('python.org')
    False

    >>>se_puede_acceder_a_url('https://www.python.org')
    True
    """
    try:
        respuesta = urllib2.urlopen(url_)
        return respuesta.code == 200
    except (urllib2.HTTPError, urllib2.URLError) as error:
        LOGGER.warning('Error al acceder a la URL %s. Error: %s', url_, error)
        return False

def abrir_url_en_navegador(br, url_, cookies_=None):
    u'''
    Devuelve si es posible abir la URL (cookies opcionales)
    en el 'navegador' proporconado por Mechanize.
    '''
    intentos = 0
    conectado = False
    while not conectado:
        try:
            br.open(url_)
            if cookies_ is not None:
                for cookie in cookies_:
                    br.set_cookie(cookie)
                br.open(url_)
            conectado = True
            return conectado
        except (mechanize.HTTPError, mechanize.URLError, urllib2.URLError) as error:
            LOGGER.info('Error al abrir la URL %s. \nError: %s. \nIntentando nuevamente.', url_, error)
            intentos += 1
            if intentos > 4:
                #LOGGER.warning('Error al abrir la URL %s. Abortado.', url_)
                return False
def obtener_cookies_validas(cookies_):
    u'''
    Devuelve un diccionario de cookies si estas fueron ingresadas
    respetando el orden AAA=YYY;XXX=BBB.
    '''
    #dict_cookies = {}
    lista_cookies = cookies_.split(';')
    for cookie in lista_cookies:
        cookie_y_valor = cookie.split('=')
        if len(cookie_y_valor) != 2:
            LOGGER.critical('Error con el formato de la cookie %s. No cumple el formato.', cookie)
            return None
        if cookie_y_valor[0] == '' or cookie_y_valor[1] == '':
            LOGGER.critical('Error con el formato de la cookie %s. Falta nombre o valor.', cookie)
            return None
    return lista_cookies

def obtener_links_validos_desde_url(url_, cookies_=None):
    '''
    Devuelve un diccionario de objetos Links con todas las URLs encontradas
    a partir de la original con todos sus datos para poder analizar vulnerabilidades
    XSS.
    '''
    br = mechanize.Browser()
    configurar_navegador(br)
    if not abrir_url_en_navegador(br, url_, cookies_) or not es_url_valida(url_) or es_url_prohibida(url_):
        LOGGER.warning('Error al abrir la URL %s. Abortado.', url_)
        return dict()
    links = list()
    links_usados = list()
    cola_links = Queue.Queue()
    url_parseado = urlparse.urlparse(url_)
    _compilar_regex(r'(?!^//|\bhttp\b)[A-Za-z0-9_\-//]*\.\w*',
                    r'(?!^//|\bhttp\b)([A-Za-z0-9_\-\/]*\/[A-Za-z0-9_\-\.\/]*)',
                    r'.*\b' + url_parseado.hostname.replace('www.', r'\.?') + r'\b(?!\.)'
                   )
    links.append(url_)
    for link in br.links():
        links.append(link.url)
    for link in links:
        if es_url_prohibida(link):
            continue
        link_valido = obtener_link_valido(url_, link, url_parseado.scheme)
        if not link_valido:
            continue
        if es_url_valida(link_valido) and link_valido and abrir_url_en_navegador(br, link_valido) and link_valido not in links_usados:
            links_usados.append(link_valido)
            objeto_link = Links(link_valido)
            try:
                objeto_link.html = br.response().read()
            except httplib.IncompleteRead as error:
                LOGGER.critical('Error al obtener el HTML de la URL: %s.\nError: %s.', link_valido, error)
                #print error, link_valido
            objeto_link.scripts = obtener_scripts_desde_url(link_valido, url_parseado.scheme, objeto_link.html)
            objeto_link.entradas = obtener_entradas_desde_url(objeto_link.html)
            objeto_link.parametros = obtener_parametros_de_la_url(link_valido)
            #links_utiles[link_valido] = objeto_link
            cola_links.put(objeto_link)
            LOGGER.info('URL agregada correctamente! %s.', link_valido)
    return cola_links

def main():
    u'''
    A partir de una URL (cookies opcionales) se obtinen todas sus links pertenecientes a la misma
    con sus datos.
    '''
    url_ingresada = sys.argv[1]
    cookies_ingresadas = None
    if not es_url_valida(url_ingresada):
        sys.exit("Esquema de URL invalido. Ingrese nuevamente.")
    if not se_puede_acceder_a_url(url_ingresada):
        sys.exit("No se puede acceder a la URL. Revise la conexion o el sitio web.")
    if len(sys.argv) > 2:
        cookies_ingresadas = sys.argv[2]
        if not obtener_cookies_validas(cookies_ingresadas):
            sys.exit('Error con las cookies ingresadas. Revise el formato "xxx=yyy;"')
    obtener_links_validos_desde_url(url_ingresada, cookies_ingresadas)

if __name__ == '__main__':
    main()
