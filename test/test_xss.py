#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import re
import xss

RE_DOMXSS_SOURCES = re.compile(r'(location\s*[\[.])|([.\[]\s*["\']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)')
RE_DOMXSS_SINKS = re.compile(r'((src|href|data|location|code|value|action)\s*["\'\]]*\s*\+?\s*=)|((replace|assign|navigate|getResponseHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["\'\]]*\s*\()')
RE_DOMXSS_SINKS_JQUERY = re.compile(r'/after\(|\.append\(|\.before\(|\.html\(|\.prepend\(|\.replaceWith\(|\.wrap\(|\.wrapAll\(|\$\(|\.globalEval\(|\.add\(|jQUery\(|\$\(|\.parseHTML\(/')


class XssTest(unittest.TestCase):
    u'''Test para xss.py'''
    def test_obtener_payloads(self):
        u'''Test para ver si se cargan bien las payloads del archivo'''

        lista = ['''"\\"><imG/sRc=l oNerrOr=(prompt)() x>",''',
                 '''"<!--<iMg sRc=--><img src=x oNERror=(prompt)`` x>",''',
                 u'''"<deTails oNToggle=confi\\u0072m()>",''']

        self.assertEqual(xss.obtener_payloads(),
                         lista
                        )

    def test_buscar_vulnerabilidad_xss_en_url(self):
        u'''Test para ver si se encuentra una vulnerabilidad en la URL'''

        self.assertTrue(xss.buscar_vulnerabilidad_xss_en_url('https://google-gruyere.appspot.com/201813828985/snippets.gtl?uid=brie',
                                                             {'uid':['brie']},
                                                             u'''"<deTails oNToggle=confi\u0072m()>",'''
                                                            )
                       )

    def test_script_analizado_previamente(self):
        u'''Test para revisar si se evita el doble escaneo de un mismo script encontrado
        en distintas URLs'''

        self.assertFalse(xss.script_analizado_previamente('''<script>alert(1)</script>'''))
        self.assertTrue(xss.script_analizado_previamente('''<script>alert(1)</script>'''))


    def test_buscar_vulnerabilidades_dom_xss(self):
        u'''Test para buscar vulnerabilidades DOM Based en un script'''

        script = """document.write('<a href="https://www.gambling.com/bJuo_GA7331V2"
                    title="21 Grand Casino" target="_blank"><img width="300" height="250" border="0" alt="21 Grand Casino"
                    src="https://www.gambling-affiliation.com/uploads/ads/22759.gif"></a>');"""

        self.assertEqual(xss.buscar_vulnerabilidades_dom_xss(script),
                         {1:['.write(', 'href='], 3:['src=']}
                        )
        self.assertEqual(xss.buscar_vulnerabilidades_dom_xss('''ga('create', 'UA-71981724-1', 'auto');ga('send', 'pageview');'''),
                         {}
                        )

    def test_obtener_vulnerabilidades_dom_xss(self):
        u'''Test para buscar vulnerabilidades DOM Based en un línea de un script'''

        script = """parent.frames[target].location.href = href;"""

        self.assertEqual(xss.obtener_vulnerabilidades_dom_xss(script, RE_DOMXSS_SOURCES),
                         ['location.']
                        )
        self.assertEqual(xss.obtener_vulnerabilidades_dom_xss(script, RE_DOMXSS_SINKS),
                         ['href =']
                        )
        self.assertEqual(xss.obtener_vulnerabilidades_dom_xss(script, RE_DOMXSS_SINKS_JQUERY),
                         []
                        )

if __name__ == '__main__':
    unittest.main()
