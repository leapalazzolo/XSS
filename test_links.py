import unittest
import links

class LinksTest(unittest.TestCase):
    """Test para 'links.py'"""

    def test_url_google_valida(self):
        self.assertTrue(links.es_url_valida('http://www.google.com'))

    def test_url_google_ar_valida(self):
        self.assertTrue(links.es_url_valida('https://www.google.com.ar'))

    def test_url_python_valida(self):
        self.assertTrue(links.es_url_valida('https://python.org'))

    def test_url_invalida(self):
        self.assertFalse(links.es_url_valida('alumno2.unlam.edu.ar/'))

    def test_acceder_a_url_google(self):
        self.assertTrue(links.se_puede_acceder_a_url('http://www.google.com'))

    def test_acceder_a_url_python(self):
        self.assertTrue(links.se_puede_acceder_a_url('https://python.org'))

    def test_acceder_a_url_invalida(self):
        self.assertFalse(links.se_puede_acceder_a_url('http://www.leandropalazzolo.org'))

    def obtner_links_validos_desde_docs_python(self): #Revisar este que anda mal
        self.assertEqual(
            links.obtener_links_validos_desde_url('http://docs.python.org'),
                                                ['http://docs.python.org', 'http://docs.python.org/about.html', 'http://docs.pyt\
                                                hon.org/bugs.html', 'http://docs.python.org/c-api/index.html', 'http://docs.pyth\
                                                on.org/contents.html', 'http://docs.python.org/copyright.html', 'http://docs.pyt\
                                                hon.org/distributing/index.html', 'http://docs.python.org/download.html', 'http:\
                                                //docs.python.org/extending/index.html', 'http://docs.python.org/faq/index.html'
                                                , 'http://docs.python.org/genindex.html', 'http://docs.python.org/glossary.html'
                                                , 'http://docs.python.org/howto/index.html', 'http://docs.python.org/installing/\
                                                index.html', 'http://docs.python.org/library/index.html', 'http://docs.python.or\
                                                g/license.html', 'http://docs.python.org/py-modindex.html', 'http://docs.python.\
                                                org/reference/index.html', 'http://docs.python.org/search.html', 'http://docs.py\
                                                thon.org/tutorial/index.html', 'http://docs.python.org/using/index.html', 'http:\
                                                //docs.python.org/whatsnew/3.6.html', 'https://docs.python.org/2.7/', 'https://d\
                                                ocs.python.org/3.5/', 'https://docs.python.org/3.7/']
                                                )
            
    def test_links_validos_unlam(self):
        self.assertEqual(
            links.obtener_links_validos_desde_url('http://www.unlam.edu.ar'),
            ['http://alumno2.unlam.edu.ar/', 'http://antigua.unlam.edu.ar', 'http://biblioteca.unlam.edu.ar/',
            'http://comunidad.unlam.edu.ar', 'http://cyt.unlam.edu.ar/',
            'http://derecho.unlam.edu.ar/', 'http://economicas.unlam.edu.ar/', 'http://formacioncontinua.unlam.edu.ar/', 'http://humanidades.unlam.edu.ar', 'http://ingenieria.unlam.edu.ar/', 'http://ingresantes.unlam.edu.ar/', 'http://miel.unlam.edu.ar/', 'http://observatoriosocial.unlam.edu.ar/', 'http://posgrado.unlam.edu.ar',
            'http://reddi.unlam.edu.ar/index.php/reddi', 'http://repositoriocyt.unlam.edu.ar/', 'http://rince.unlam.edu.ar/', 'http://salud.unlam.edu.ar/', 'http://www.unlam.edu.ar', 'http://www.unlam.edu.ar/index.php', 'http://www.unlam.edu.ar/index.php?seccion=-1&accion=curso',
            'http://www.unlam.edu.ar/index.php?seccion=-1&accion=difusion&idDestacado=8987', 'http://www.unlam.edu.ar/index.php?seccion=-1&accion=difusion&idDestacado=9047', 'http://www.unlam.edu.ar/index.php?seccion=-1&accion=difusion&idDestacado=9056', 'http://www.unlam.edu.ar/index.php?seccion=-1&accion=difusion&idDestacado=9059',
            'http://www.unlam.edu.ar/index.php?seccion=-1&accion=difusion&idNoticia=9048', 'http://www.unlam.edu.ar/index.php?seccion=-1&accion=difusion&idNoticia=9049', 'http://www.unlam.edu.ar/index.php?seccion=-1&accion=difusion&idNoticia=9050', 'http://www.unlam.edu.ar/index.php?seccion=-1&accion=difusion&idNoticia=9052',
            'http://www.unlam.edu.ar/index.php?seccion=-1&accion=difusion&idNoticia=9053', 'http://www.unlam.edu.ar/index.php?seccion=1', 'http://www.unlam.edu.ar/index.php?seccion=10', 'http://www.unlam.edu.ar/index.php?seccion=11', 'http://www.unlam.edu.ar/index.php?seccion=11&idArticulo=150', 'http://www.unlam.edu.ar/index.php?seccion=11&idArticulo=151',
            'http://www.unlam.edu.ar/index.php?seccion=2', 'http://www.unlam.edu.ar/index.php?seccion=2&idArticulo=570', 'http://www.unlam.edu.ar/index.php?seccion=3', 'http://www.unlam.edu.ar/index.php?seccion=4', 'http://www.unlam.edu.ar/index.php?seccion=4&idArticulo=113',
            'http://www.unlam.edu.ar/index.php?seccion=5', 'http://www.unlam.edu.ar/index.php?seccion=6', 'http://www.unlam.edu.ar/index.php?seccion=7', 'http://www.unlam.edu.ar/index.php?seccion=8', 'http://www.unlam.edu.ar/index.php?seccion=8&idArticulo=148', 'http://www.unlam.edu.ar/index.php?seccion=8&idArticulo=449',
            'http://www.unlam.edu.ar/index.php?seccion=8&idArticulo=541', 'http://www.unlam.edu.ar/index.php?seccion=8&idArticulo=594', 'http://www.unlam.edu.ar/index.php?seccion=9', 'http://www.unlam.edu.ar/rihumso/index.php/humanidades/'])

if __name__ == '__main__':
    unittest.main()
