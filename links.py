import os
import sys
import re
import urllib2, urllib
import urlparse
import mechanize
from bs4 import BeautifulSoup, SoupStrainer


def obtener_scripts_desde_url(url, esquema, link_a_archivo, link_a_dominio_o_subdominio, cookies=None):
    br = mechanize.Browser()
    _configurar_navegador(br)
    if not abrir_url_en_navegador(br, url ,cookies):
        print "Error al abrir la URL.", url
        if cookies is not None:
            print "Revise las cookies.", cookies
        return list()
    html = br.response().read()
    bs = BeautifulSoup(html, 'lxml')
    scripts = set()
    for script in bs.findAll('script'):
        texto = script.getText()
        #print texto
        if texto != '':
            #print texto.encode("utf-8") #TODO enconde para todos los archivos
            scripts.add(texto)
        else:
            if script.has_attr('src'):
                if link_a_archivo.match(script['src']) is not None:
                    link_script = urlparse.urljoin(url, script['src'])
                    #print link_script
                    script_js =  urllib2.urlopen(link_script).read()
                    scripts.add(script_js)
                else:
                    if link_a_dominio_o_subdominio.match(script['src']) is not None:
                        #print 'Mismo dominio o subdominio: ', link.url
                        link_script = script['src']
                        if link_script[0] == '/' and link_script[1] == '/':
                            link_script.replace('//', esquema + '://')
                        #print link_script
                        script_js =  urllib2.urlopen(link_script).read()
                        scripts.add(script_js)
        #os.system('pause')
    return list(scripts)

def _configurar_navegador(browser):
    browser.addheaders = [('User-agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127 Firefox/2.0.0.11')]
    browser.set_handle_robots(False)
    browser.set_handle_refresh(False)

def es_url_valida(url):
    """Devuelve si una url se encuentra bien formada y existe conexion hacia ella.

    >>>es_url_valida('python.org')
    False

    >>>es_url_valida('https://www.python.org')
    True
    """
    url_parseado = urlparse.urlparse(url)
    #request = requests.get(url)
    return all([url_parseado.scheme, url_parseado.netloc])

def se_puede_acceder_a_url(url):
    """Devuelve si en una url existe conexion hacia ella.

    >>>se_puede_acceder_a_url('python.org')
    False

    >>>se_puede_acceder_a_url('https://www.python.org')
    True
    """
    try:
        #url_parseado = urlparse(url)
        respuesta = urllib2.urlopen(url)
        return respuesta.code == 200
    except urllib2.HTTPError, e:
        print(e.code)
        return False
    except urllib2.URLError, e:
        print(e.args)
        return False


def abrir_url_en_navegador(br, url, cookies=None):
    intentos = 0
    conectado = False
    while not conectado:
        try:
            br.open(url)
            if cookies is not None:
                #TODO: validar cookies en formato lsita ####"xxx=yyy; ""
                for cookie in cookies:
                    br.set_cookie(cookie)
                br.open(url) #TODO: try except
            conectado = True # if line above fails, this is never executed
            return conectado
        except mechanize.HTTPError as e:
            print e.code            
            intentos += 1        
            if intentos > 4:
                return False
        except mechanize.URLError as e:
            print e.reason.args            
            intentos += 1
            if intentos > 4:
                return False

def obtener_links_validos_desde_url(url, cookies=None):
    br = mechanize.Browser()
    _configurar_navegador(br)
   #cookies = ["JSESSIONID=08DA6EBFBB3136C6C893DAC963C19682.nodo01_t02", "SRV=nodo01_t02"]
    #   br.set_cookie(cookie)
    scripts = set()
    url_parseado = urlparse.urlparse(url)
    url_y_scripts = dict()
    regex_link_a_archivo = '(?!^//)[A-Za-z0-9_\-//]*\.\w*'  #TODO ver lo de r'
    regex_mismo_dominio_o_subdominio =  r'.*\b' + url_parseado.hostname.replace('www.','.?') + r'\b(?!\.)' # OK? Lo del igual es para evitar un x.com/?a=y.com y aggara el ultimo
    regex_link_a_carpeta = '(?!^//)[A-Za-z0-9_\-//]*/[A-Za-z0-9_\-\.//]*'
    
    link_a_archivo = re.compile(regex_link_a_archivo)        # Archvos con su ruta
    link_a_carpeta = re.compile(regex_link_a_carpeta)        # OK  TODO
    link_a_dominio_o_subdominio = re.compile(regex_mismo_dominio_o_subdominio)
    if not abrir_url_en_navegador(br, url ,cookies):
        print "Error al abrir la URL."
        if cookies is not None:
            print "Revise las cookies."
        return list()
    #obtener_scripts_desde_html(html, url, url_parseado.scheme, link_a_archivo, link_a_dominio_o_subdominio)
    #os.system('pause')  
    links_validos = set()
    links_validos.add(url)
    for link in br.links():
        link_valido = str()
        if link_a_archivo.match(link.url) is not None or link_a_carpeta.match(link.url) is not None:
            link_valido = urlparse.urljoin(url, link.url)
            if es_url_valida(link_valido):
            #print link_valido
                #links_validos.add(link_valido)
                if link_valido not in url_y_scripts: #TODO no es necesario, pero por si falla lo anterior
                    url_y_scripts[link_valido] = obtener_scripts_desde_url(link_valido, url_parseado.scheme, link_a_archivo, link_a_dominio_o_subdominio)
        else:
            if link_a_dominio_o_subdominio.match(link.url) is not None:
                #print 'Mismo dominio o subdominio: ', link.url
                link_valido = link.url
                if link_valido[0] == '/' and link_valido[1] == '/':
                    link_valido.replace('//', url_parseado.scheme + '://') # TODO test 
                if es_url_valida(link_valido):
                    #links_validos.add(link_valido)
                    if link_valido not in url_y_scripts:
                        url_y_scripts[link_valido] = obtener_scripts_desde_url(link_valido, url_parseado.scheme, link_a_archivo, link_a_dominio_o_subdominio)
    #print url_y_scripts
    #lista_links_validos = list(links_validos)
    #lista_links_validos.sort()
    #print lista_links_validos
    #for link in url_y_scripts:
    #    print link
    #    os.system('pause')
    #    for script in url_y_scripts[link]:
    #        print "\t", script
    #        os.system('pause')
    return url_y_scripts

if __name__ == '__main__':
    url = sys.argv[1]
    if not es_url_valida(url):
        sys.exit("Esquema de URL invalido. Ingrese nuevamente.")
    if not se_puede_acceder_a_url(url):
        pass
        #sys.exit("No se puede acceder a la URL. Revise la conexion o el sitio web.")
    obtener_links_validos_desde_url(sys.argv[1])
    #obtener_scripts_desde_url(sys.argv[1])
