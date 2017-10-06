import unittest
import mechanize
import links

class LinksTest(unittest.TestCase):
    """Test para 'links.py'"""


    def test_obtener_parametros_de_la_url(self):
        '''
        Test de la funcion obtener_parametros_de_la_url
        '''
        url_unlam = 'http://www.unlam.edu.ar/index.php'
        url_unlam_con_parametros = 'http://www.unlam.edu.ar/index.php?seccion=-1&accion=buscador'
        url_google_con_parametros = 'https://www.google.com.ar/?gfe_rd=cr&dcr=0&ei=eUXWWZPVGcb_8AfYso_wAw&gws_rd=ssl'

        self.assertEqual(links.obtener_parametros_de_la_url(url_unlam_con_parametros),
                         {'seccion':['-1'], 'accion':['buscador']}
                        )
        self.assertEqual(links.obtener_parametros_de_la_url(url_unlam),
                         {}
                        )
        self.assertEqual(links.obtener_parametros_de_la_url(url_google_con_parametros),
                         {'gfe_rd':['cr'], 'dcr':['0'], 'ei':['eUXWWZPVGcb_8AfYso_wAw'], 'gws_rd':['ssl']}
                        )

    def test_obtener_scripts_desde_url(self):

        url_blogger = 'https://www.blogger.com/about/?r=2'
        dominio_blogger = 'https'
        archivo_html_blogger = open('blogger_html.txt', 'r')
        html_blogger = archivo_html_blogger.read()
        archivo_scripts_blogger_1 = open('blogger_script_1.txt', 'r')
        scripts_blogger_1 = archivo_scripts_blogger_1.read()
        archivo_scripts_blogger_2 = open('blogger_script_2.txt', 'r')
        scripts_blogger_2 = archivo_scripts_blogger_2.read()
        lista_scripts_blogger = [str(scripts_blogger_1), str(scripts_blogger_2)]
        links._compilar_regex(r'(?!^//|\bhttp\b)[A-Za-z0-9_\-//]*\.\w*', #TODO test
                              '(?!^//|\bhttp\b)([A-Za-z0-9_\-\/]*\/[A-Za-z0-9_\-\.\/]*)',
                              r'.*\b' + 'www.blogger.com'.replace('www.', r'\.?') + r'\b(?!\.)'
                             )
        self.assertNotEqual(links.obtener_scripts_desde_url(url_blogger, dominio_blogger, html_blogger),
                         lista_scripts_blogger
                        )
    
    def test_obtener_link_valido(self):
        links._compilar_regex(r'(?!^//)[A-Za-z0-9_\-//]*\.\w*',
                              '([A-Za-z0-9_\-\/]*\/[A-Za-z0-9_\-\.\/]*)',
                              r'.*\b' + 'www.blogger.com'.replace('www.', '\.?') + r'\b(?!\.)'
                              )
        url_blogger = 'https://www.blogger.com/about/?r=2'
        dominio_blogger = 'https'
        link = '/go/createyourblog'
        
        self.assertEqual(links.obtener_link_valido(url_blogger, link, dominio_blogger),
                         'https://www.blogger.com/go/createyourblog'
                        )
        self.assertEqual(links.obtener_link_valido(url_blogger, '/', dominio_blogger),
                         'https://www.blogger.com/'
                        )
    def test_obtener_entradas_desde_url(self):
        url_unlam = 'http://alumno2.unlam.edu.ar/index.jsp?pageLand=registrarse'
        html_unlam = open('unlam_html.txt', 'r').read()
        parametros = links.obtener_entradas_desde_url(html_unlam)
        parametro = parametros[0][0]['id']
        self.assertEqual(parametro,
                        'docume'
                        )
    def test_es_url_prohibida(self):

        self.assertTrue(links._es_url_prohibida('http://example.com/asd/imagen.jpg'))
        
        self.assertFalse(links._es_url_prohibida('http://example.com/asd/noespng.html'))
    
    def test_es_url_valida(self):

        self.assertFalse(links.es_url_valida('python.org'))
    
        self.assertTrue(links.es_url_valida('https://www.python.org'))    

    def test_se_puede_acceder_a_url(self):

            self.assertFalse(links.se_puede_acceder_a_url('https://sitioquenoesasfasdasda.org'))
        
            self.assertTrue(links.se_puede_acceder_a_url('https://www.python.org')) 

    def test_abrir_url_en_navegador(self):
        br = mechanize.Browser()
        links.configurar_navegador(br)
        self.assertFalse(links.abrir_url_en_navegador(br, 'https://sitioquenoesasfasdasda.org'))

        self.assertTrue(links.abrir_url_en_navegador(br, 'https://www.python.org')) 

        self.assertTrue(links.abrir_url_en_navegador(br, 'https://cart.dx.com/')) 

        self.assertTrue(links.abrir_url_en_navegador(br, 'https://cart.dx.com/', 'DXGlobalization_lang=en;DXGlobalization_locale=en-US;DXGlobalization_currency=ARS'))

    def test_validar_formato_cookies(self):

        self.assertTrue(links.validar_formato_cookies('DXGlobalization_lang=en;DXGlobalization_locale=en-US;DXGlobalization_currency=ARS'))
        
        self.assertFalse(links.validar_formato_cookies('DXGlobalization_lang=en;'))

        self.assertFalse(links.validar_formato_cookies('DXGlobalization_lang='))

if __name__ == '__main__':
    unittest.main()
