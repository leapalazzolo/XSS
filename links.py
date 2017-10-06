import sys
import re
import httplib
import urllib2
import urlparse
import mechanize
from bs4 import BeautifulSoup


REGEX_ARCHIVO, REGEX_CARPETA, REGEX_DOMINIO_O_SUBDOMINIO = None, None, None
BLACKLIST = ['.png', '.jpg', '.jpeg', '.mp3', '.mp4', '.gif', '.svg',
             '.pdf', '.doc', '.docx', '.zip', '.rar', '.rss', '.js', '.min.js']
             #TODO ver que los iltimos no sean esos

class Links(object):
    '''
    Clase que posee todos la informacion necesaria para
    analizar la existencia de una vulnerabilidad XSS sobre
    una URL.
    '''
    def __init__(self, url_):
        self._url = url_
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
        return self._parametros

    @parametros.setter
    def parametros(self, parametros):
        self._parametros = parametros

def _compilar_regex(regex_link_a_archivo, regex_link_a_carpeta, regex_dominio_o_subdominio):
    '''
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
    html_parseado = BeautifulSoup(html, 'lxml')
    scripts = set()
    for script in html_parseado.findAll('script'):
        texto = script.getText()
        if texto != '':
            scripts.add(texto)
        else:
            if script.has_attr('src'):
                link_script = obtener_link_valido(url_, script['src'], esquema)
                if link_script is not None:
                    try:
                        script_js = urllib2.urlopen(link_script).read()
                        scripts.add(script_js)
                    except (urllib2.HTTPError, ValueError) as error:
                        print 'Error obteniendo el script: ', link_script
                        print 'Detales: ', error
    return list(scripts)

def obtener_link_valido(url_, link, esquema):
    '''
    Devuelve el link en formato URL en caso de que pertenezca a la misma
    o a un subdominio.
    '''                                         #TODO: no deberia revisar aca si es un .js
    link_valido = None
    if REGEX_ARCHIVO.match(link) is not None or REGEX_CARPETA.match(link) is not None:
        link_valido = urlparse.urljoin(url_, link)
    else: 
        if REGEX_DOMINIO_O_SUBDOMINIO.match(link) is not None and link != '/':
            link_valido = link
            if link_valido[0] == '/' and link_valido[1] == '/':
                link_valido = link_valido.replace('//', esquema + '://')
            if '#' in link_valido:
                link_valido = link_valido[:link_valido.index('#')]
    return link_valido

def obtener_entradas_desde_url(html):
    '''
    Devuelve los 'inputs' encontrados en los 'form' del html que son posibles de
    ingresar texto y explotar una vulnerabilidad XSS.
    '''
    nro_form = 0
    forms_y_parametros = dict()
    html_parseado = BeautifulSoup(html, 'lxml')
    listform = ['radio', 'checkbox', 'text', 'password', 'email', 'url', 'search', 'hidden']
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

def _es_url_prohibida(url_):
    '''
    Devuelve si una URL es un archivo el cual no es
    necesario/posible inyectar un payload XSS.
    '''

    for extension in BLACKLIST:
        if extension in url_[-len(extension):]:
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
        #url_parseado = urlparse(url)
        respuesta = urllib2.urlopen(url_)
        return respuesta.code == 200
    except (urllib2.HTTPError, urllib2.URLError) as error:
        print error
        return False

def abrir_url_en_navegador(br, url_, cookies_=None):
    '''
    Devuelve si es posible abir la URL (cookies opcionales)
    en el navegador proporconado por Mechanize.
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
            print 'Error al abrir URL. Intentando nuevamente.', error
            intentos += 1
            if intentos > 4:
                return False
def validar_formato_cookies(cookies_):
    lista_cookies = cookies_.split(';')
    for cookie in lista_cookies:
        cookie_y_valor = cookie.split('=')
        if len(cookie_y_valor) != 2:
            return False    #TODO pasar a None con las opcs
        if cookie_y_valor[0] == '' or cookie_y_valor[1] == '':
            return False
    return lista_cookies

def obtener_links_validos_desde_url(url_, cookies_=None):
    '''
    Devuelve un diccionario de objetos Links con todas las URLs encontradas
    a partir de la original con todos sus datos para poder analizar vulnerabilidades
    XSS.
    '''
    br = mechanize.Browser()
    configurar_navegador(br)
    if not abrir_url_en_navegador(br, url_, cookies_) or not es_url_valida(url_) or _es_url_prohibida(url_):
        print "Error al abrir la URL."
        if cookies_ is not None:
            print "Revise las cookies."
        return dict()
    links = list()
    links_utiles = dict()
    #cookies = ["JSESSIONID=76E51C2E3C449FB79D5F032071E89D19.nodo01_t01", "SRV=nodo01_t01"]
    url_parseado = urlparse.urlparse(url_)
    _compilar_regex(r'(?!^//|\bhttp\b)[A-Za-z0-9_\-//]*\.\w*', #TODO test
                    '(?!^//|\bhttp\b)([A-Za-z0-9_\-\/]*\/[A-Za-z0-9_\-\.\/]*)',
                    r'.*\b' + url_parseado.hostname.replace('www.', r'\.?') + r'\b(?!\.)'
                   )
    links.append(url_)
    for link in br.links():
        links.append(link.url)
    for link in links:
        if _es_url_prohibida(link):
            continue
        link_valido = obtener_link_valido(url_, link, url_parseado.scheme)
        if not link_valido:
            continue
        if es_url_valida(link_valido) and link_valido not in links_utiles and abrir_url_en_navegador(br, link_valido):
            objeto_link = Links(link_valido)
            try:
                objeto_link.html = br.response().read()
            except httplib.IncompleteRead as error:
                print error, link_valido
            objeto_link.scripts = obtener_scripts_desde_url(link_valido, url_parseado.scheme, objeto_link.html)
            objeto_link.entradas = obtener_entradas_desde_url(objeto_link.html)
            objeto_link.parametros = obtener_parametros_de_la_url(link_valido)
            links_utiles[link_valido] = objeto_link
    print len(links_utiles)
    for link in links_utiles:
        print len(links_utiles[link].scripts)
        print links_utiles[link].parametros
        print links_utiles[link].entradas
        print links_utiles[link].url
    br.close()
    return links_utiles

if __name__ == '__main__':
    url_ = sys.argv[1]
    cookies_ = None
    if not es_url_valida(url_):
        sys.exit("Esquema de URL invalido. Ingrese nuevamente.")
    if not se_puede_acceder_a_url(url_):
        sys.exit("No se puede acceder a la URL. Revise la conexion o el sitio web.")
    if len(sys.argv) > 2:
        cookies_ = sys.argv[2]
        if not validar_formato_cookies(cookies_):
            sys.exit('Error con las cookies ingresadas. Revise el formato "xxx=yyy;"')
    obtener_links_validos_desde_url(url_, cookies_)
    #obtener_scripts_desde_url(sys.argv[1])
