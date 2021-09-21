# Crawler_com_Framework_Scrapy_Sigalei
### Crawler no framwork Scrapy que retorna o md5 dos PDFs de Inteiro Teor dos últimos 3 dias do site da câmara e grava em um banco SQLite

***
## Explicação do Projeto

* __PROBLEMA__ :arrow_right: Conferir se os documentos de *Inteiro Teor* das proposições (*PEC, PLP ou PL*) mais recentes foram baixados corretamente nos últimos três dias.
* __SOLUÇÃO__ :arrow_right: Sistema que receba o tipo de proposição desejada (*PEC, PLP ou PL*) e retorne uma lista de hash MD5 gerada a partir dos documentos de Inteiro Teor das proposições apresentadas nos últimos três dias na Câmara dos Deputados. Essa hash é utilizada para verificar se aquele documento já foi baixado ou não.

***

## Como executar o projeto:

Crie um ambiente virtual:

```
virtualenv -p python.exe env
env\Scripts\activate.bat
```

Depois instale as *libs* do projeto:

```
pip freeze > requirements.txt
```

Com o ambiente virtual ativado e com as *libs* instaladas digite no terminal `  scrapy crawl sigalei_spider  `

<pre>
(env) E:\SIGALEI>scrapy crawl sigalei_spider
...
DIGITE A PROPOSICAO (PL. PLP ou PEC): <b>INSIRA AQUI A PROPOSICAO QUE DESEJA PESQUISAR</b> (pode ser minúsculo)
...
</pre>

:arrow_right: Como resultado, uma banco *SQLite* é criado com uma tabela *sigalei* da proposição escolhida.

***
## Explicando o Crawler:

1) No site oficial da [Câmara dos Deputados](https://www.camara.leg.br/busca-portal/proposicoes/pesquisa-simplificada) uma __API__ é consumida para retornar um *dicionário* com a resposta referente aos parâmetros passados.

CONTINUAR DAQUI

