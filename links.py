import os
import sys
import re
import httplib
import urllib2, urllib
import urlparse
import mechanize
from bs4 import BeautifulSoup, SoupStrainer

blacklist = ['.png', '.jpg', '.jpeg', '.mp3', '.mp4', '.gif', '.svg',
             '.pdf', '.doc', '.docx', '.zip', '.rar', '.rss']#, '.js', '.min.js']
             #TODO ver que los iltimos no sean esos

class Links(object):
    '''
    '''
    def __init__(self, url_):
        self._url = url_
        self._esquema = str()
        self._scripts = list()
        self._entradas = dict()
        self._html = str()
        self._parametros = dict()

    @property
    def url(self):
        return self._url

    @property
    def scripts(self):
        return self._scripts
    
    @scripts.setter
    def scripts(self, script):
        self._scripts.append(script)

    @property
    def html(self):
        return self._html
    
    @html.setter
    def html(self, html):
        self._html = html

    @property    
    def entradas(self):
        return self.entradas
    
    @entradas.setter
    def entradas(self, entradas):
        self._entradas = entradas
    
    @property    
    def parametros(self):
        return self.parametros
    
    @parametros.setter
    def entradas(self, parametros):
        self._parametros = parametros

def obtener_parametros_de_la_url(query):
    parametros = urlparse.parse_qs(query,keep_blank_values=True)



def obtener_scripts_desde_url(url, esquema, html, link_a_archivo, link_a_dominio_o_subdominio, cookies=None):#, cookies=None):
    #br = mechanize.Browser()
    #configurar_navegador(br)
    #if not abrir_url_en_navegador(br, url ,cookies):
    #    print "Error al abrir la URL.", url
    #    if cookies is not None:
    #        print "Revise las cookies.", cookies
    #    return list()
    #html = br.response().read()
    bs = BeautifulSoup(html, 'lxml')
    scripts = set()
    for script in bs.findAll('script'):
        texto = script.getText()
        #print texto
        if texto != '':
            #print texto.encode("utf-8") #TODO enconde para todos los archivos
            scripts.add(texto)
            #print texto[0:5]
        else:
            if script.has_attr('src'):
                if link_a_archivo.match(script['src']) is not None:
                    try:
                        link_script = urlparse.urljoin(url, script['src'])
                        #print link_script
                        script_js =  urllib2.urlopen(link_script).read()
                        scripts.add(script_js)
                    except urllib2.HTTPError, error:
                        print error, url
                        pass
                else:
                    if link_a_dominio_o_subdominio.match(script['src']) is not None:
                        try: #print 'Mismo dominio o subdominio: ', link.url
                            link_script = script['src']
                            if link_script[0] == '/' and link_script[1] == '/':
                                link_script = link_script.replace('//', esquema + '://')
                            #print link_script
                            script_js =  urllib2.urlopen(link_script).read()
                            scripts.add(script_js)
                        except urllib2.HTTPError, error:
                            print error, url
                            pass
        #os.system('pause')
    return list(scripts)


def obtener_entradas_desde_url(br, html):
    nro_form = 0
    forms_y_parametros = dict()
    bs = BeautifulSoup(html, 'lxml')

    #try:
    #    forms = br.forms()
    #except (ValueError, mechanize._form.ParseError) as error:
    #    print error
    #    return forms_y_parametros TODO hidden
    listform = ['radio', 'checkbox','text', 'password', 'email', 'url', 'search', 'hidden', '']

    for form in bs.findAll('form'):  
        #br.select_form(nr=nro_form)    # submit the first form
        #controls = form.controls
        lista_parametros =  form.findAll('input', {'type':''}) + form.findAll('input', {'type':listform}) + form.findAll('textarea')
        #for parametro in form.findAll('input'), {'type':'text'}:
            #if '<Text' or '<Password' or '<Check' or '<Radio' or '<Select' in str(parametro): #TODO ver esto
            #print parametro.name, parametro.type, parametro.id
            #if 'TextControl' in str(parametro) or 'TextareaControl' in str(parametro):
        #    lista_parametros.append(parametro)
        #    print parametro['name']
        #print lista_parametros
        if lista_parametros:
            forms_y_parametros[nro_form] = lista_parametros
        nro_form += 1
    return forms_y_parametros

def configurar_navegador(browser):
    browser.addheaders = [('User-agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127 Firefox/2.0.0.11')]
    browser.set_handle_robots(False)
    browser.set_handle_refresh(False)
    #browser.add_handler(PrettifyHandler()) TODO VER ACA
    #browser.add_handler(PrettifyHandler())
    #browser.set_handle_redirect(True) #TODO VEr aca

def es_url_prohibida(url):
    for extension in blacklist:
        if extension in url:
            return True
    return False


def es_url_valida(url):
    """Devuelve si una url se encuentra bien formada y existe conexion hacia ella.

    >>>es_url_valida('python.org')
    False

    >>>es_url_valida('https://www.python.org')
    True
    """
    url_parseado = urlparse.urlparse(url)
    #root, ext = os.path.splitext(url_parseado.path)
    #request = requests.get(url)
    return all([url_parseado.scheme, url_parseado.netloc, not es_url_prohibida(url)])

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
        except (mechanize.HTTPError,mechanize.URLError, urllib2.URLError) as error:
            print 'URL invalida', error            
            intentos += 1        
            if intentos > 4:
                return False

def obtener_links_validos_desde_url(url, cookies=None):
    br = mechanize.Browser()#factory=mechanize.DefaultFactory(i_want_broken_xhtml_support=True))
    configurar_navegador(br)
    if not abrir_url_en_navegador(br, url ,cookies) or not es_url_valida(url):
        print "Error al abrir la URL."
        if cookies is not None:
            print "Revise las cookies."
        return list()
    
    #cookies = ["JSESSIONID=76E51C2E3C449FB79D5F032071E89D19.nodo01_t01", "SRV=nodo01_t01"]
    #br.set_cookie(cookie)
    url_parseado = urlparse.urlparse(url)
    #root, extension = os.path.splitext(url_parseado)
    #url_y_scripts = dict()
    regex_link_a_archivo = '(?!^//)[A-Za-z0-9_\-//]*\.\w*'  #TODO ver lo de r'
    regex_mismo_dominio_o_subdominio =  r'.*\b' + url_parseado.hostname.replace('www.','\.?') + r'\b(?!\.)' # OK? Lo del igual es para evitar un x.com/?a=y.com y aggara el ultimo
    regex_link_a_carpeta = '(?!^//)[A-Za-z0-9_\-//]*/[A-Za-z0-9_\-\.//]*'
    
    link_a_archivo = re.compile(regex_link_a_archivo)        # Archvos con su ruta
    link_a_carpeta = re.compile(regex_link_a_carpeta)        # OK  TODO
    link_a_dominio_o_subdominio = re.compile(regex_mismo_dominio_o_subdominio)
    #obtener_scripts_desde_html(html, url, url_parseado.scheme, link_a_archivo, link_a_dominio_o_subdominio)
    #os.system('pause')  
    #print url
    links = list()
    #url = url if url[-1] == '/' else url +'/'
    links.append(url)
    for link in br.links():
        links.append(link.url)
    #links_validos = set()
    #print links
    links_utiles = dict()
    for link in links:
        #print link
        link_valido = str()
        #print link #TODO TODO TODO ver el / al final de la url para que no repita
        #TODO TODO TODO TODO Filtrar urls antes
        if link_a_archivo.match(link) is not None or link_a_carpeta.match(link) is not None: #br.links() y link.url
            link_valido = urlparse.urljoin(url, link)
            #print link_valido
            if '#' in link_valido:
                link_valido = link_valido[:link_valido.index('#')]
                #print '#'
            #link_valido = link_valido if link_valido[-1] == '/' else link_valido +'/'
            if es_url_valida(link_valido):
                #links_validos.add(link_valido)
                if link_valido not in links_utiles: #TODO no es necesario, pero por si falla lo anterior
                    
                    print link_valido
                    if abrir_url_en_navegador(br, link_valido):
                        objeto_link = Links(link_valido)
                        try:
                            objeto_link.html = br.response().read()#obtener_scripts_desde_url(link_valido, url_parseado.scheme, link_a_archivo, link_a_dominio_o_subdominio)
                        except httplib.IncompleteRead as error:
                            print error, link_valido
                        objeto_link.scripts = obtener_scripts_desde_url(link_valido, url_parseado.scheme, objeto_link.html, link_a_archivo, link_a_dominio_o_subdominio)
                        objeto_link.entradas = obtener_entradas_desde_url(br, objeto_link.html)
                        links_utiles[link_valido] = objeto_link
        else:
            if link_a_dominio_o_subdominio.match(link) is not None:
                #print 'Mismo dominio o subdominio: ', link
                #link_valido = link if link[-1] == '/' else link + '/'
                link_valido = link
                if link_valido[0] == '/' and link_valido[1] == '/':
                    link_valido.replace('//', url_parseado.scheme + '://') # TODO test 
                    #link_valido = link_valido[:link_valido.index('#')] if '#' in link_valido else link_valido
                if '#' in link_valido:
                    link_valido = link_valido[:link_valido.index('#')] + '/'
                    #print '#'
                if es_url_valida(link_valido):
                    #links_validos.add(link_valido)
                    print link_valido
                    if link_valido not in links_utiles: #TODO no es necesario, pero por si falla lo anterior
                        #print link_valido
                        if abrir_url_en_navegador(br, link_valido):
                            #urls_y_html[link_valido] = br.response().read()
                            #print link_valido
                            objeto_link = Links(link_valido)
                            #TODO excep abajo
                            try:
                                objeto_link.html = br.response().read()#obtener_scripts_desde_url(link_valido, url_parseado.scheme, link_a_archivo, link_a_dominio_o_subdominio)
                            except httplib.IncompleteRead as error:
                                print error, link_valido
                            
                            #objeto_link.html = br.response().read()#obtener_scripts_desde_url(link_valido, url_parseado.scheme, link_a_archivo, link_a_dominio_o_subdominio)
                            objeto_link.scripts = obtener_scripts_desde_url(link_valido, url_parseado.scheme, objeto_link.html, link_a_archivo, link_a_dominio_o_subdominio)
                            objeto_link.entradas = obtener_entradas_desde_url(br, objeto_link.html)
                            links_utiles[link_valido] = objeto_link
                            #print urls_y_html[link_valido]
                    #if link_valido not in url_y_scripts:
                    #    url_y_scripts[link_valido] = obtener_scripts_desde_url(link_valido, url_parseado.scheme, link_a_archivo, link_a_dominio_o_subdominio)
    #print url_y_scripts
    #lista_links_validos = list(links_validos)
    #lista_links_validos.sort()
    #print lista_links_validos
    #archivo = open('test.txt', 'w+')
    print len(links_utiles)
    for link in links_utiles:
        #print link
        #archivo.write(links_utiles[link].html)
        #print links_utiles[link].html
        #print links_utiles[link].scripts
        #archivo.write(links_utiles[link].scripts)
        #archivo.write(links_utiles[link].parametros)
        params = links_utiles[link].parametros
        for form in params:
            print form
            for param in params[form]:
                print param
        #archivo.write(links_utiles[link].url)
        print links_utiles[link].url
        os.system('pause')
    #archivo.close()
    #print urls_y_html
    return links_utiles
    #return list(link_validos)

if __name__ == '__main__':
    url = sys.argv[1]
    if not es_url_valida(url):
        sys.exit("Esquema de URL invalido. Ingrese nuevamente.")
    if not se_puede_acceder_a_url(url):
        sys.exit("No se puede acceder a la URL. Revise la conexion o el sitio web.")
    obtener_links_validos_desde_url(sys.argv[1])
    #obtener_scripts_desde_url(sys.argv[1])
