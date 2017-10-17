# Challenge XSS

'Challenge XSS' es un script hecho en Python que, a partir de una URL dada, se encarga de obtener todos los links a los que hace referencia siempre y cuando estos pertenezcan al dominio o algún subdominio de ella. Una vez obtenidos, los analizará en busca de vulnerabilidades XSS, las cuales serán guardadas en una base de datos local y única por cada ejecución.

## Getting Started

### Requisitos

Python 2.7
```
Mechanize
BeautifulSoup
```

### Instalación

Descargar el proyecto

```
git clone https://github.com/leapalazzolo/XSS.git
```

Navegar hasta el directorio

```
cd xss
```

Instalar lo requerido

```
python setup.py
```

Ejecutar

```
python xss.py -u http://example.com -t N [-c] [-d] [-r]

optional arguments:
  -h, --help            												show this help message and exit
  -v, --version         												show program's version number and exit
  -c Nombre=valor;Nombre=valor, --cookies Nombre=valor;Nombre=valor		Las cookies para la URL ingresada.
  -d, --dom             												Análisis estatico DOM Based XSS de los scripts
																		encontrados en la URL.
  -r, --reflected       												Seleccionar un análisis XSS Reflected.

required named arguments:
  -u http://example.com, --url http://example.com
																		La URL en la cual se basara el análisis.
  -t N, --threads N     												La cantidad de threads para realizar la búsqueda de
																		vulnerabilidades.

En caso de que no se especifique el tipo de análisis, se hará por defecto
solamente del tipo XSS Reflected.
```

## Test

Para ejecutar los tests automáticos, desde el directorio raíz:

```
python -m unittest test.test_links
```

```
python -m unittest test.test_xss
```

## Desarrollo

### Desarrollado

* Obtención de links pertenecientes al dominio de URL junto con sus datos relevantes
* Escaneo estático de vulnerabilidades DOM Based XSS
* Escaneo de vulnerabilidades XSS Reflected
* Escaneo de vulnerabilidades en parámetros de la URL

### Mejoras

* Uso de threads para obtener links: Actualmente el uso de threads es para el escaneo de vulnerabilidades aunque podría ampliarse a la obtención de links .
* "Escaneo" de vulnerabilidades XSS Stored: En la primer versión final del script se descartó la búsqueda de este tipo debido a que su implementación previamente realizada mediante un webdriver (selenium) ralentizaba significativamente los tiempos de ejecución y aumentaba su consumo de recursos sin dar mejores resultados. Su funcionamiento era, a través de un navegador, detectar mensajes de alerta inmediatamente después de ser ingresados a través del script (debido a las restricciones con JavaScript sobre el navegador, pocas "inyecciones" llegaban a destino).
* Multithread en SQLite: Actualmente el acceso a la base de datos es serializado mediante una conexión compartida entre threads y el uso de semáforos, por lo que se podría dar una mejor solución mediante el uso de un sistema productor-consumidor.



## Autor

* **Leandro Palazzolo** - (leapalazzolo@gmail.com)


## Licencia

Este proyecto se encuentra licenciado bajo MIT License - [LICENSE.md](LICENSE.md).

## Conclusión final

Realizar este proyecto ha sido:
* totalmente provechoso debido a la incorporación de nuevos conceptos y consolidación de antiguos.
* un desafío debido a la naturaleza del mismo, requisitos y plazo de tiempo.
* un puntapié inicial para próximos proyectos de la misma índole.


