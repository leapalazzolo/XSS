#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import threading
import time
import codecs
import urllib
import argparse
import urlparse
import logging
import urllib2
import httplib
import Queue
import links
import mechanize
import selenium
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys

logging.config.fileConfig('log.ini')
LOGGER = logging.getLogger('root')

blacklist = ['.png', '.jpg', '.jpeg', '.mp3', '.mp4', '.gif', '.svg',
             '.pdf', '.doc', '.docx', '.zip', '.rar', '.rss']

LISTA_PAYLOADS = []
RE_DOMXSS_SOURCES = re.compile("""/(location\s*[\[.])|([.\[]\s*["']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)/""")
RE_DOMXSS_SINKS = re.compile("""/((src|href|data|location|code|value|action)\s*["'\]]*\s*\+?\s*=)|((replace|assign|navigate|getResponseHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["'\]]*\s*\()/""")   

class Worker(threading.Thread):
    u'''
    Clase que instanciará los threads encargados de realizar el trabajo
    '''
    def __init__(self, cola_links, cookies, *args):
        self.cola_links = cola_links
        threading.Thread.__init__(self, *args)
    def run(self):
        '''
        Busca vulnerabilidades XSS en la URL y sus componenetes mientras haya URLs pendientes.
        '''
        while not cola_links.empty():
            link = self.cola_links.get(timeout=3)
            LOGGER.info(u'Empieza el análisis con la URL: %s', link.url)
            buscar_vulnerabilidad_xss(link, cookies)
            if link.parametros:
                LOGGER.info('Analizando parametros en lla misma URL: %s', link.url)    
                inyectar_payload_en_url(link.url, link.parametros)
            if link.scripts:
                LOGGER.info('Buscando vulnerabilidades DOM Based estaticamente en la URL: %s', link.url)
                buscar_xss_dom(link.scripts) #TODO ver duplicados
            #TODO agregar a cola de vulenrables
        LOGGER.info('Analisis finalizado de URL: %s', link.url)

def obtener_payloads():
    u'''
    Devuelve la lista de payloads pasada a través de un archivo txt
    para facilitar su mantenimiento.
    '''
    lista_payloads = []
    try:
        with open('payloads.txt', 'r') as archivo_payloads:
            for linea in archivo_payloads.readlines():
                lista_payloads.append(linea)
    except EnvironmentError, error:
        LOGGER.critical('Error al cargar las payloads: %s', error)
    finally:
        return lista_payloads
        

def obtener_vulnerabilidades_xss_dom(linea, regex, tipo):
    u'''
    Devuelve la lista de vulnerabilidades del tipo DOM Based encontradas
    según la regex pasada (análisis pasivo de SINK o SOURCE) junto con su posición en la línea
    del script proporcionado.
    '''
    lista_vulnerabilidades = list()
    lista_posiciones = list()
    for patron in regex.finditer(linea, re.MULTILINE):
        for grupo in patron.groups():
            posicion = str(patron.span())
            if grupo is not None and posicion not in lista_posiciones:
                lista_posiciones.append(posicion)
                lista_vulnerabilidades.append(tipo + ' encontrado' + posicion + ': ' +  grupo)
    return lista_vulnerabilidades

def buscar_xss_dom(scripts):
    u'''
    Devuelve un diccionario con las vulnerabilidades DOM XSS encontradas a través de una analisis 
    estatico con su numero de linea y su posicion de inicio y fin de la misma. 
    '''
    nro_linea = 0
    dict_xss_dom = dict()
    for script in scripts: #TODO ver que no haga 2 veces el mismo archio
        lista_xss_dom = list()
        for linea in script.split('\n'):
            nro_linea += 1
            lista_xss_dom = obtener_vulnerabilidades_xss_dom(linea, RE_DOMXSS_SOURCES, 'Source')
            lista_xss_dom += obtener_vulnerabilidades_xss_dom(linea, RE_DOMXSS_SINKS, 'Sink')
            
            if lista_xss_dom:
                dict_xss_dom[nro_linea] = lista_xss_dom
                LOGGER.debug('Posible vulnerabilidad DOM Based en la URL')
    # print dict_xss_dom
    return dict_xss_dom

def detectar_xss_reflejado(br, payload):
    u'''
    Devuelve si existe una vulnerabilidad XSS REFLECTED a partir de encontrar
    el payoad previamente ingresado en el HTML de la respuesta.
    '''
    try:
        if payload in br.response().read(): #TODO: XSS reflejado
            return True
        return False
    except httplib.IncompleteRead as error:
        LOGGER.critical('Error al obtener respuesta de la URL. Error: %s', error)
        return False

def buscar_xss_reflejado(br, payload, entrada, form):
    #for paylaod in LISTA_PAYLOADS:
        #print parametro.type
        #os.system('pause')
    #print br
    inyectar_payload(br, payload, entrada)
    #br.form[entrada['id']] = payload #TODO ver lo del name e id
    #br.submit()
    if payload in br.response().read():#detectar_xss_reflejado(br, payload):
        #TODO log, bdd, etc.
        print "XSS encontrado: ",
        br.back() #TODO: Ver si srive afuera del if anterior este bloque
        br.select_form(nr=form)
        '''
        if payload in br.response().read():#detectar_xss_reflejado(br, payload):
            print "Stored"      #XSS encontrado al inyectar payload y luego de esto#TODO
            LOGGER.info('Vulnerabilidad Stored XSS en la URL.')
            #TODO volar el Stored falopa
            return True
        else:
            LOGGER.info('Vulnerabilidad Reflected XSS en la URL.')
            print "Reflejado"   #XSS encontrado solo al inyectar payload #TODO
            return True'''
    else:
        return None

def buscar_xss_almacenado(driver, payload, entrada):

    try:
        if entrada.has_attr('id'):
            entrada_elem = driver.find_element_by_id(entrada['id']) #TODO ver id y name
            return detectar_xss_almacenado(driver, entrada_elem, payload)
        else:
            if entrada.has_attr['name']:
                entrada_elem = driver.find_element_by_name(entrada['name'])
    except (NoSuchElementException, KeyError) as error:
        LOGGER.critical('Error al procesar: %s', error)
        return None
    except TypeError as error:
        LOGGER.critical('Error al procesa el elemento: %s', entrada)
        return None
    

def detectar_xss_almacenado(driver, parametro, payload):
    '''
    '''
    parametro.send_keys(payload)
    parametro.submit()
    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present(),
                                    'Timed out waiting for PA creation ' +
                                    'confirmation popup to appear.')
        #os.system('pause')
        driver.switch_to.alert.accept()
        print('XSS STORED')
        return True
    #    os.system('pause')
    except NoAlertPresentException:
        return None
    except TimeoutException: #TODO mejorar aca
        return None
    except:
        return None

def inyectar_payload(br, payload, entrada): #NO hace falta determinar si es get o post.
    try:
        if entrada.has_attr('id'):
            br.form[entrada['id']] = payload #TODO ver lo del name e id
            br.submit()
        else:
            if entrada.has_attr('name'):
                br.form[entrada['name']] = payload #TODO ver lo del name e id
                br.submit()
    except (ValueError, urllib2.URLError) as error:
        print error
        LOGGER.warning('Error al intentar explotar : %s', entrada)
        print 'Error al enviar el control: ', entrada

def inyectar_payload_en_url(url_, parametros):
    br = mechanize.Browser()#factory=mechanize.RobustFactory())  #TODO factory=mechanize.RobustFactory()
    links.configurar_navegador(br)
    url_parseado = list(urlparse.urlparse(url_))
    for indice_parametro, valores in parametros.items():
        for indice_valor, valor in enumerate(valores):
            for payload in LISTA_PAYLOADS:
                nuevos_valores = dict(parametros)
                nuevos_valores[indice_parametro][indice_valor] = valor + urllib.quote_plus(payload)
                #print nuevos_valores
                url_parseado[4] = urllib.urlencode(nuevos_valores)
                nueva_url = urlparse.urlunparse(url_parseado)
                print nueva_url
                if links.abrir_url_en_navegador(br, nueva_url):
                    if detectar_xss_reflejado(br, payload):
                        print 'XSS by URL', payload
                        LOGGER.info('Vulnerabilidad Reflected XSS en parametros URL.')
                        #os.system('pause')

def buscar_vulnerabilidad_xss(objeto_link, cookies):
    br = mechanize.Browser()#factory=mechanize.RobustFactory())  #TODO factory=mechanize.RobustFactory()
    links.configurar_navegador(br)
    lista_cookies, dict_cokies = links.validar_formato_cookies(cookies)
    if not links.abrir_url_en_navegador(br, objeto_link.url, lista_cookies):
        print "Error al abrir la URL." #TODO no deberia pasar esto
        if cookies is not None:
            print "Revise las cookies."
        return False
    try:
        driver = webdriver.Firefox()    #TODO dividir esto 
        driver.get(objeto_link.url) #TODO es solo una vez esto
        if cookies is not None:
            driver.add_cookie(dict_cokies)
    except selenium.common.exceptions.WebDriverException as error:
        LOGGER.critical('Error al carcar el webdriver. Error: %s', error)
    forms_y_entradas = objeto_link.entradas
    for form in forms_y_entradas:     # if a form exists, submit it
        #params = form#list(br.forms())[0]    # our form
        br.select_form(nr=form)    # submit the first form
        lista_entradas = forms_y_entradas[form]
        #print 'Form: ', form
        for entrada in lista_entradas:
            p = 0
            encontrado = False          
            while p < len(LISTA_PAYLOADS) and not encontrado:
                payload = LISTA_PAYLOADS[p]
                resultado = buscar_xss_reflejado(br, payload, entrada, form)
                p += 1
                if resultado:
                    print 'Encontradoooooo'
                    encontrado = True
                else:
                    br.back()
                    br.select_form(nr=form)
                    resultado = buscar_xss_almacenado(driver, payload, entrada)
                    if resultado:
                        print 'Encontradoooo2'
                        encontrado = True
    br.close()
    driver.quit()

if __name__ == '__main__':
    LISTA_PAYLOADS = obtener_payloads()
    if LISTA_PAYLOADS == []:
        LOGGER.critical('Error al cargar las payloads: Revise el archivo payloads.txt.')
        sys.exit(1)
    if not links.es_url_valida(sys.argv[1]): #TODO: chequear url antes de la lista o cuando se va a hacer lo de xss?
        LOGGER.critical('Esquema de URL invalido. Ingrese nuevamente.')
        sys.exit(1)
    if not links.se_puede_acceder_a_url(sys.argv[1]):
        LOGGER.critical('No se puede acceder a la URL. Revise la conexion o el sitio web.')
        sys.exit(1)
    cookies = None
    if sys.argv[2]:
        cookies = sys.argv[2]
    cola_links = links.obtener_links_validos_desde_url(sys.argv[1], cookies)
    threads = []
    LOGGER.info('EMPIEZA el programa')
    for i in range(1):
        worker = Worker(cola_links, cookies)
        threads.append(worker)
        #cworker.setDaemon(True)
        worker.start()

    
    for t in threads:
        t.join()

    print 'All work is done'
            #buscar_vulnerabilidad_xss(objeto_link, payloads) #TODO ver si pasar objeto o partes
        #os.system('pause')
        
def main():
    descripcion = ''
    """
    """
    parser = argparse.ArgumentParser(description=descripcion, prog='PROG', usage='%(prog)s [options]', epilog='')
    parser.add_argument('-u',
                        '--url',
                        metavar='http://example.com',
                        type=str,
                        help='La URL en la cual se basara el analisis.',
                        action='store',
                        dest='url'
                        )
    parser.add_argument('-c',
                        '--cookies',
                        metavar='Nombre=valor Nombre=valor',
                        type=str,
                        nargs='*',
                        help='Las cookies para la URL ingresada.',
                        action='store',
                        dest='cookies'
                        )#TODO testear cookies
    parser.add_argument('-d',
                        '--dom',
                        help='Seleccionar un analisis estatico DOM Based XSS.',
                        action='store_true',
                        dest='dom'
                        )
    
    parser.add_argument('-s',
                        '--simple',
                        help='Seleccionar un analisis XSS Reflected, Stored y DOM Based.',
                        action='store_true',
                        dest='reflected'
                        )
    
    parser.add_argument('-t',
                        '--threads',
                        metavar='N',
                        type=int,
                        help='La cantidad de threads para realizar la busqueda de vulnerabilidades.',
                        action='store',
                        dest='threads'
                        )
