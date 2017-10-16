# Challenge XSS

'Challenge XSS' es un script hecho en Python que, a partir de una URL dada, se encarga de obtener todos los links a los que hace referencia siempre y cuando estos pertenezcan al dominio o algún subdominio de ella. Una vez obtenidos, los analizará en busca de vulnerabilidades XSS, las cuales serán guardadas en una base de datos local y única por cada ejecución.

## Getting Started

### Prerequisites

```
Mechanize
BeautifulSoup
lxml
```

### Installing

Descargar el proyecto

```
git clone https://github.com/leapalazzolo/XSS.git
```

Navegar hasta el directorio

```
cd XSS
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
  -t N, --threads N     La cantidad de threads para realizar la búsqueda de
                        vulnerabilidades.

En caso de que no se especifique el tipo de análisis, se hará por defecto
solamente del tipo XSS Reflected.
```

## Running the tests

Para ejecutar los tests automáticos (desde el directorio raíz)

```
python -m unittest test.test_links
```

```
python -m unittest test.test_xss
```

## Deployment

### Developed


### Future


Add additional notes about how to deploy this on a live system


## Authors

* **Leandro Palazzolo** - (leapalazzolo@gmail.com)


## License

Este proyecto se encuentra licenciado bajo MIT License - [LICENSE.md](LICENSE.md).

## Acknowledgments

Realizar este proyecto ha sido:
* totalmente provechoso debido a la incorporación de nuevos conceptos y consolidación de antiguos.
* un desafío debido a la naturaleza del mismo, requisitos y plazo de tiempo.
* un puntapié inicial para próximos proyectos de la misma índole.


