import sys
import os
import threading
import time
import codecs
import urllib
import urlparse
import logging
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
from selenium.webdriver.common.keys import Keys

logging.config.fileConfig('log.ini')

blacklist = ['.png', '.jpg', '.jpeg', '.mp3', '.mp4', '.gif', '.svg',
             '.pdf', '.doc', '.docx', '.zip', '.rar', '.rss']

#payloads = ['<script>alert(1)</script>', '<IMG SRC=/ onerror="alert(String.fromCharCode(88,83,83))"></img>', 'javascript:alert(1)']

#DOM_FILTER_REGEX = r"(?s)<!--.*?-->|\bescape\([^)]+\)|\([^)]+==[^(]+\)|\"[^\"]+\"|'[^']+'"

#RE_DOMXSS_SOURCES = re.compile('(location\s*[\[.])|([.\[]\s*["\']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)')
#RE_DOMXSS_SINKS = re.compile('((src|href|data|location|code|value|action)\s*["\'\]]*\s*\+?\s*=)|((replace|assign|navigate|getResponseHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["\'\]]*\s*\()')
RE_DOMXSS_SOURCES = re.compile("""/(location\s*[\[.])|([.\[]\s*["']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)/""")
RE_DOMXSS_SINKS = re.compile("""/((src|href|data|location|code|value|action)\s*["'\]]*\s*\+?\s*=)|((replace|assign|navigate|getResponseHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["'\]]*\s*\()/""")   

class Worker(threading.Thread):
    def __init__(self, cola_links, lista_payloads, *args, **kwargs):
        self.cola_links = cola_links
        self.lista_payloads = lista_payloads
        threading.Thread.__init__(self, *args, **kwargs)
    def run(self):
        while not cola_links.empty():
            link = self.cola_links.get(timeout=3)  # 3s timeout
            print link.url
            print len(link.scripts)
            print link.parametros
            print link.entradas
            buscar_vulnerabilidad_xss(link, payloads)
            #except Queue.Empty:
                #print 'No hay mas trabajo'
            # do whatever work you have to do on work
        print 'Fin del trabajo'
def crear_logger():
    global logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('xss.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)


def cargar_payloads():
    lista_payloads = []
    try:
        with open('payloads.txt', 'r') as archivo_payloads:
            for linea in archivo_payloads.readlines():
                lista_payloads.append(linea)
                #print linea
        return lista_payloads
    except EnvironmentError, error:
        print error

def obtener_vulnerabilidades_xss_dom(linea, regex, tipo):
    lista_vulnerabilidades = list()
    lista_posiciones = list()
    for patron in regex.finditer(linea, re.MULTILINE):
        for grupo in patron.groups():
            posicion = str(patron.span())
            if grupo is not None and posicion not in lista_posiciones:
                lista_posiciones.append(posicion)
                lista_vulnerabilidades.append(tipo + ' encontrado' + posicion + ': ' +  grupo)
    #print lista_vulnerabilidades
    #os.system('pause')
    return lista_vulnerabilidades

def detectar_xss_DOM(scripts):
    '''
    Devuelve un diccionario con las vulnerabilidades DOM XSS encontradas a travrs de una analisis estatico
    con su numero de linea y su posicion ed inicio y fin de la misma. 
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
    # print dict_xss_dom
    return dict_xss_dom

def detectar_xss_reflejado(br, payload):
    if payload in br.response().read(): #TODO: XSS reflejado
        #os.system('pause')
        #br.back()
        return True
    #br.back()
    return False

def buscar_xss_reflejado(br, payload, entrada, form):
    #for paylaod in lista_payloads:
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
        if payload in br.response().read():#detectar_xss_reflejado(br, payload):
            print "Stored"      #XSS encontrado al inyectar payload y luego de esto#TODO
            return True
        else:
            print "Reflejado"   #XSS encontrado solo al inyectar payload #TODO
            return True
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
        return None
    

def detectar_xss_almacenado(driver, parametro, payload):
    #entradas = driver.find_elements_by_xpath("//input") #TODO: tipo de texto
    #entradas = driver.find_elements_by_tag_name('input')
    #print entradas.tag_name, len(entradas)
    #inputElement = driver.find_element_by_id(parametro.id)
    #encontrado = False
    #print str(entradas)#, entradas
        #print driver.current_url
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

    except ValueError, error:
        print error
        print 'Error al enviar el control: ', entrada

def inyectar_payload_en_url(br, url_, payload, parametros):
    url_parseado = list(urlparse.urlparse(url_))
    print '\n\n\n\n\n'
    for indice_parametro, valores in parametros.items():
        for indice_valor, valor in enumerate(valores):
            for payload in payloads:
                nuevos_valores = dict(parametros)
                nuevos_valores[indice_parametro][indice_valor] = valor + urllib.quote_plus(payload)
                #print nuevos_valores
                url_parseado[4] = urllib.urlencode(nuevos_valores)
                nueva_url = urlparse.urlunparse(url_parseado)
                print nueva_url
                if links.abrir_url_en_navegador(br, nueva_url):
                    if payload in br.response().read():
                        print 'XSS by URL', payload
                        os.system('pause')

def buscar_vulnerabilidad_xss(objeto_link, lista_payloads, cookies=None):



    #print threading.currentThread().getName(), 'Starting'
    #for extension in blacklist:
    #    if extension in url_ingresada:
    #        return False YA LO HACE LINKS
    
    #driver = webdriver.Firefox()
    #driver.get(url)
    #if cookies is not None:
    #    driver.manage().addCookie(cookies)
    br = mechanize.Browser()#factory=mechanize.RobustFactory())  #TODO factory=mechanize.RobustFactory()
    #links.configurar_navegador(br)
    br.addheaders = [('User-agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127 Firefox/2.0.0.11')]
    br.set_handle_robots(False)
    br.set_handle_refresh(False)
    if not links.abrir_url_en_navegador(br, objeto_link.url, cookies):
        print "Error al abrir la URL." #TODO no deberia pasar esto
        if cookies is not None:
            print "Revise las cookies."
        return False

        #i = 0
    driver = webdriver.Firefox()    #TODO dividir esto 
    driver.get(objeto_link.url) #TODO es solo una vez esto
    if cookies is not None:
        driver.manage().addCookie(cookies)
    forms_y_entradas = objeto_link.entradas
    #print forms_y_entradas
    #forms = br.forms() 
    for form in forms_y_entradas:     # if a form exists, submit it
        #params = form#list(br.forms())[0]    # our form
        br.select_form(nr=form)    # submit the first form
        lista_entradas = forms_y_entradas[form]
        #print 'Form: ', form
        for entrada in lista_entradas:
            #print entrada
            #print str(parametro)
            #par = str(p)
            # submit only those forms which require text
            #print parametro.name, parametro.type, parametro.id
            #if 'TextControl' in str(parametro) or 'TextareaControl' in str(parametro):
            
            p = 0
            encontrado = False
            #inyectar_payload_en_url(br, objeto_link.url, lista_payloads, objeto_link.parametros)
            '''if entrada.has_attr('id'):
                entrada = entrada['id']
            else:
                if entrada.has_attr['name']:
                    entrada = entrada['name']
                else:
                    continue'''
            
            while p < len(lista_payloads) and not encontrado:
                #print parametro.type
                #os.system('pause')
                #print entrada
                #print br'''
                payload = lista_payloads[p]
                #entrada = entrada['id'] if entrada.has_attr('id') else entrada
                
                resultado = buscar_xss_reflejado(br, payload, entrada, form)
                if resultado:
                    print 'Encontradoooooo'
                    encontrado = True
                else:
                    #br.back()      #TODO xss_hard
                    #br.select_form(nr=form)
                    resultado = buscar_xss_almacenado(driver, payload, entrada)
                    '''try:
                        entrada_elem = driver.find_element_by_id(entrada) #TODO ver id y name
                        if detectar_xss_almacenado(driver, entrada_elem, payload):
                            encontrado = True
                    except (NoSuchElementException, KeyError) as error:
                        print error'''
                    if resultado:
                        print 'Encontradoooo2'
                        encontrado = True
                        #driver.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w') #TODO esto
                            
                br.back()
                br.select_form(nr=form)
                p += 1
                #else:
                #    br.back()
                #    br.select_form(nr=i)
    br.close()
    driver.quit()
    #print threading.currentThread().getName(), 'Exiting'

def worker(link, payloads):
    while not cola_links.empty():
        try:
            link = cola_links.get()
            print link.url
            print len(link.scripts)
            print link.parametros
            print link.entradas
            print threading.currentThread().getName(), 'Staring'
            buscar_vulnerabilidad_xss(link, payloads)
            print threading.currentThread().getName(), 'Exiting'
            #ohbjeto_link = cola_links.get()
           #Worker(cola_links, payloads).start()
        except KeyboardInterrupt:
            print 'Cerrando...'


if __name__ == '__main__':
    #url = sys.argv[1]
    #logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='xss.log')
    #crear_logger()
    payloads = cargar_payloads()
    if not payloads:
        logging.critical('Error al cargar las payloads: Archivo payloads.txt no encontrado.')
        sys.exit(1)
    if payloads == []:
        logging.critical('Error al cargar las payloads: Archivo vacio o incompatible.')
        sys.exit(1)
    if not links.es_url_valida(sys.argv[1]): #TODO: chequear url antes de la lista o cuando se va a hacer lo de xss?
        logging.critical('Esquema de URL invalido. Ingrese nuevamente.')
        sys.exit(1)
    if not links.se_puede_acceder_a_url(sys.argv[1]):
        logging.critical('No se puede acceder a la URL. Revise la conexion o el sitio web.')
        sys.exit(1)
    #print sys.argv[1]
    cola_links = links.obtener_links_validos_desde_url(sys.argv[1])
    threads = []
    #for url in urls_encontradas:
    #while not cola_links.empty():
        #print url
    for i in range(2):
        print 'EMPIEZA\n'
        worker = Worker(cola_links, payloads)
        threads.append(worker)
        worker.setDaemon(True)
        worker.start()

    
    for t in threads:
        t.join()

    print 'All work is done'
            #buscar_vulnerabilidad_xss(objeto_link, payloads) #TODO ver si pasar objeto o partes
        #os.system('pause')
        

