# Challenge XSS

'Challenge XSS' es un script hecho en Python que, a partir de una URL dada, se encarga de obtener todos los links a los que hace referencia siempre y cuando estos pertenezcan a la URL misma o un subdominio de ella. Una vez obtenidos, los analizará en busca de vulnerabilidades XSS, las cuales serán guardadas en una base de datos local y única por cada ejecución.

## Getting Started


git clone https://github.com/leapalazzolo/XSS.git
cd XSS ..
python xss.py -u http://example.com -t 2 [-c] [-d]

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
python xss.py -u http://example.com -t 2 [-c] [-d]
```

## Running the tests

Para ejecutar los tests automáticos, entrar a 

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds


## Authors

* **Leandro Palazzolo** - (leapalazzolo@gmail.com)


## License

Este proyecto se encuentra licenciado bajo MIT License - [LICENSE.md](LICENSE.md).

## Acknowledgments

Realizar este proyecto ha sido:
* totalmente provechoso debido a la incorporación de nuevos conceptos y consolidación de antiguos.
* un desafío debido a la naturaleza del mismo, requisitos y plazo de tiempo.
* un puntapié inicial para próximos proyectos de la misma índole.


