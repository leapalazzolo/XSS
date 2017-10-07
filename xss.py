import sys
import os
import time
import codecs
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

blacklist = ['.png', '.jpg', '.jpeg', '.mp3', '.mp4', '.gif', '.svg',
             '.pdf', '.doc', '.docx', '.zip', '.rar', '.rss']

#payloads = ['<script>alert(1)</script>', '<IMG SRC=/ onerror="alert(String.fromCharCode(88,83,83))"></img>', 'javascript:alert(1)']

#DOM_FILTER_REGEX = r"(?s)<!--.*?-->|\bescape\([^)]+\)|\([^)]+==[^(]+\)|\"[^\"]+\"|'[^']+'"

#RE_DOMXSS_SOURCES = re.compile('(location\s*[\[.])|([.\[]\s*["\']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)')
#RE_DOMXSS_SINKS = re.compile('((src|href|data|location|code|value|action)\s*["\'\]]*\s*\+?\s*=)|((replace|assign|navigate|getResponseHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["\'\]]*\s*\()')
RE_DOMXSS_SOURCES = re.compile("""/(location\s*[\[.])|([.\[]\s*["']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)/""")
RE_DOMXSS_SINKS = re.compile("""/((src|href|data|location|code|value|action)\s*["'\]]*\s*\+?\s*=)|((replace|assign|navigate|getResponseHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["'\]]*\s*\()/""")   

#TODO singleton

def detectar_WAF():
    noise = "<script>alert()</script>" #a payload which is noisy enough to provoke the WAF
    fuzz = URL.replace("d3v", noise) #Replaces "d3v" in url with noise
    res1 = urlopen(fuzz) #Opens the noise injected payload
    if res1.code == 406 or res1.code == 501: #if the http response code is 406/501
        print"\033[1;31m[-]\033[1;m WAF Detected : Mod_Security"
        print "\033[1;33m[!]\033[1;m Delaying requests to avoid WAF detection\n"
        WAF = "True" #A WAF is present
        waf_choice()
    elif res1.code == 999: #if the http response code is 999
        print"\033[1;31m[-]\033[1;m WAF Detected : WebKnight"
        print "\033[1;33m[!]\033[1;m Delaying requests to avoid WAF detection\n"
        WAF = "True"
        waf_choice()
    elif res1.code == 419: #if the http response code is 419
        print"\033[1;31m[-]\033[1;m WAF Detected : F5 BIG IP"
        print "\033[1;33m[!]\033[1;m Delaying requests to avoid WAF detection\n"
        WAF = "True"
        waf_choice()
    elif res1.code == 403: #if the http response code is 403
        print "\033[1;31m[-]\033[1;m Unknown WAF Detected"
        print "\033[1;33m[!]\033[1;m Delaying requests to avoid WAF detection\n"
        WAF = "True"
        waf_choice()
    elif res1.code == 302: #if redirection is enabled
        print "\033[1;31m[-]\033[1;m Redirection Detected! Exploitation attempts may fail.\n"
        choice()
    else:
        print "\033[1;32m[+]\033[1;m WAF Status: Offline\n"
        WAF = "False" #No WAF is present
        choice()

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
                print lista_xss_dom
                os.system('pause')
    # print dict_xss_dom
    return dict_xss_dom

def detectar_xss_reflejado(br, payload):
    if payload in br.response().read(): #TODO: XSS reflejado
        #os.system('pause')
        #br.back()
        return True
    #br.back()
    return False

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
        return False
    except TimeoutException: #TODO mejorar aca
        return False
    except:
        return False
    finally:
        driver.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')
        #driver.execute_script("window.history.go(-1)")
        #return True
def inyectar_payload(br, payload, parametro): #NO hace falta determinar si es get o post.
    try:
        br.form[parametro] = payload #TODO ver lo del name e id
        br.submit()
    except ValueError, error:
        print error
        print 'Error al enviar el control: ', parametro


def buscar_vulnerabilidad_xss(objeto_link, lista_payloads, cookies=None):

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

    '''driver = webdriver.Firefox()    #TODO dividir esto 
    driver.get(objeto_link.url)
    if cookies is not None:
        driver.manage().addCookie(cookies)'''
    

    #i = 0
    forms_y_entradas = objeto_link.entradas
    #print forms_y_entradas
    #forms = br.forms() 
    for form in forms_y_entradas:     # if a form exists, submit it
        #params = form#list(br.forms())[0]    # our form
        br.select_form(nr=form)    # submit the first form
        lista_entradas = forms_y_entradas[form]
        print 'Form: ', form
        for entrada in lista_entradas:
            print entrada['name']
            #print str(parametro)
            #par = str(p)
            # submit only those forms which require text
            #print parametro.name, parametro.type, parametro.id
            #if 'TextControl' in str(parametro) or 'TextareaControl' in str(parametro):
            
            p = 0
            encontrado = False
            while p < len(lista_payloads) and not encontrado:
                #print parametro.type
                #os.system('pause')
                print p
                #print br
                payload = lista_payloads.pop(p)
                print payload
                inyectar_payload(br, payload, entrada['name'])
                #br.form[entrada['id']] = payload #TODO ver lo del name e id
                #br.submit()
                if detectar_xss_reflejado(br, payload):
                    #TODO log, bdd, etc.
                    print "XSS encontrado: ",
                    encontrado = True
                    br.back() #TODO: Ver si srive afuera del if anterior este bloque
                    br.select_form(nr=form)
                    if detectar_xss_reflejado(br, payload):
                        print "Stored"      #XSS encontrado al inyectar payload y luego de esto
                    else:
                        print "Reflejado"   #XSS encontrado solo al inyectar payload 
                else:
                    br.back()
                    br.select_form(nr=form)
                #print br
                '''
                else:
                    try:
                        entrada = driver.find_element_by_id(entrada['id']) #TODO ver id y name
                        if detectar_xss_almacenado(driver, entrada, payload):
                            encontrado = True
                    except NoSuchElementException as error:
                        print error
                        pass
                    br.back()
                    br.select_form(nr=form)
                    #TODO: setup.py con selenium'''
                p += 1
                #else:
                #    br.back()
                #    br.select_form(nr=i)
                    


    #i += 1
        #print i
    br.close()
    #driver.quit()

if __name__ == '__main__':
    #url = sys.argv[1]
    payloads = cargar_payloads()
    if not payloads:
        sys.exit('Error al cargar las payloads.Revise el archivo.')
    if payloads == []:
        sys.exit("No se encontraron paylods. Revise el archivo 'payloads.txt' en la carpeta raiz.")
    if not links.es_url_valida(sys.argv[1]): #TODO: chequear url antes de la lista o cuando se va a hacer lo de xss?
        sys.exit("Esquema de URL invalido. Ingrese nuevamente.")
    if not links.se_puede_acceder_a_url(sys.argv[1]):
        sys.exit("No se puede acceder a la URL. Revise la conexion o el sitio web.")
    #print sys.argv[1]
    cola_links = links.obtener_links_validos_desde_url(sys.argv[1])
    
    #for url in urls_encontradas:
    while not cola_links.empty():
        #print url
        print 'EMPIEZA'
        objeto_link = cola_links.get()
        print objeto_link.url
        print len(objeto_link.scripts)
        print objeto_link.parametros
        print objeto_link.entradas
        buscar_vulnerabilidad_xss(objeto_link, payloads) #TODO ver si pasar objeto o partes
        os.system('pause')
        

