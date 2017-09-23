import sys
import re
import urllib2, urllib
import urlparse
from mechanize import Browser

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

def obtner_links_validos_desde_url(url):
    br = Browser()
    br.addheaders = [
        ('User-agent',
        'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127 Firefox/2.0.0.11')
                    ]
    print url
    br.set_handle_robots(False)
    br.set_handle_refresh(False)
    br.open(url)
    #conn = urllib.urlopen(url)
    #html = conn.read()
    #html_parseado = BeautifulSoup(html, 'lxml')
    url_parseado = urlparse.urlparse(url)
    hostname = url_parseado.hostname

    regex_link_a_archivo = '(?!^//)[A-Za-z0-9_\-//]*\.\w*'
    regex_mismo_dominio_o_subdominio =  '.*\\b' + hostname.replace('www.','.?') + '\\b(?!\.)' # OK? Lo del igual es para evitar un x.com/?a=y.com y aggara el ultimo
    regex_link_a_carpeta = '(?!^//)[A-Za-z0-9_\-//]*/[A-Za-z0-9_\-\.//]*'
    
    link_a_archivo = re.compile(regex_link_a_archivo)        # Archvos con su ruta
    link_a_carpeta = re.compile(regex_link_a_carpeta)        # OK  TODO
    link_a_dominio_o_subdominio = re.compile(regex_mismo_dominio_o_subdominio)

    # ... Exception URLERROR    
    links_validos = set()
    links_validos.add(url)
    for link in br.links():
        link_valido = str()
        if link_a_archivo.match(link.url) is not None or link_a_carpeta.match(link.url) is not None:
            link_valido = urlparse.urljoin(url, link.url)
            #print link_valido
            links_validos.add(link_valido)
        else:
            if link_a_dominio_o_subdominio.match(link.url) is not None:
                #print 'Mismo dominio o subdominio: ', link.url
                link_valido = link.url
                links_validos.add(link_valido)
    #        else:
    #            print "Nada?: ", link.url
                #Si es con //, remover
                    #Sino, OK
    return list(links_validos)

if __name__ == '__main__':
    url = sys.argv[1]
    if not es_url_valida(url):
        sys.exit("Esquema de URL invalido. Ingrese nuevamente.")
    if not se_puede_acceder_a_url(url):
        sys.exit("No se puede acceder a la URL. Revise la conexion o el sitio web.")
    obtner_links_validos_desde_url(sys.argv[1])
