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

O *spider* __sigalei_spider__ foi desenvoldo para fazer os *scrapes* dos dados solicitados das *PLs, PLPs ou PECs*.

## :arrow_forward:  Arquivo - sigalei_spider.py

1) No site oficial da [Câmara dos Deputados](https://www.camara.leg.br/busca-portal/proposicoes/pesquisa-simplificada) uma __API__ é consumida para retornar um *dicionário* com a resposta referente aos parâmetros passados.
   <br></br>
   O *crawler* não começa com o método *parse(self, response)* consumindo uma lista de *start_urls*, mas sim com *start_requests(self)* .

## * start_requests()

Faz um primeiro __POST__ com os parâmetros da API (__*order, ano, pagina, tiposDeProposicao*__) no site da Câmara e recebe um __JSON de resposta__ com .

A url que passamos os parâmetros é: ` https://www.camara.leg.br/api/v1/busca/proposicoes/_search `

Passa como parâmetros do *payload*:

* o ano_atual → como há recesso parlamentar no final do ano, não há riscos de perder propostas nos 3 primeiros dias do ano.
* o tipo de proposição → *PL, PLP ou PEC*.
* o número da página → __1__.
* a string "data" → para ordenar a resposta pela *data* mais recente.

Passa como parâmetros do *headers*:

* application/json → informando o Content-Type
* um user agent → da *lib fake-useragent*. O método *random* passa *user-agents* de forma aleatória (google, firefox, IE, Safari ...)

É feito um __yield__ *scrapy.Request* onde são passados → url, 'POST', payload, header e também a proposição buscada como meta e um callback chamando o método seguinte *update_query()*.

```
 def start_requests(self):
        lista_proposicoes = ['PL', 'PLP', 'PEC']
        tipo_proposicao = input("DIGITE A PROPOSICAO (PL, PLP ou PEC): ").upper().strip()
        while tipo_proposicao not in lista_proposicoes:
            print('')
            print(f'==> {tipo_proposicao} NAO E UMA DAS PROPOSICOES DISPONIVEIS')
            tipo_proposicao = input("==> DIGITE UMA DAS SEGUINTES PROPOSICOES (PL, PLP ou PEC): ").upper().strip()
        payload = {
            "order": "data",
            "ano": self.ano_atual,
            "pagina": 1,
            "tiposDeProposicao": tipo_proposicao
        }
        yield scrapy.Request(
            url='https://www.camara.leg.br/api/v1/busca/proposicoes/_search',
            method='POST',
            body=json.dumps(payload),
            headers=self.headers,
            meta={'tipo_proposicao': tipo_proposicao},
            callback=self.update_query
        )
```
2) Com a resposta da __API__ são estraídos → quantidade total de poposições, quantidade por páginas e quantidade de páginas.

## * update_query()

Um novo acesso à __API__ só que dessa vez iterando passando cada página como parâmetro no *payload*.
<br></br>
É feito um __yield__ *scrapy.Request* onde são passados → url, 'POST', payload, header e dessa vez além proposição buscada como meta, também é paassado o nº iterado, e um callback chamando o método seguinte *sigalei_crawler()*.
   
```
    def update_query(self, response):
        resp_json = json.loads(response.body)
        tipo_proposicao = response.meta['tipo_proposicao']
        qtd_total = resp_json['aggregations']['ano']['buckets'][0]['doc_count']
        qtd = len(resp_json['hits']['hits'])
        qtd_pags = ceil(qtd_total / qtd)
        n_i = 1
        while n_i < qtd_pags:
            payload = {
                        "order": "data",
                        "ano": self.ano_atual,
                        "pagina": n_i,
                        "tiposDeProposicao": tipo_proposicao
                    }
            yield scrapy.Request(
                url='https://www.camara.leg.br/api/v1/busca/proposicoes/_search',
                method='POST',
                body=json.dumps(payload),
                headers=self.headers,
                meta={'qtd_pags': qtd_pags,
                      'n_i': n_i},
                callback=self.sigalei_crawler
            )
            n_i += 1
```
***
3) Com a resposta para cada página é feita uma comparação entre a data pequisada (*data do dia - 3*) e a última data da proposição de cada página.

## * sigalei_crawler()

Caso a última data da página seja menor que a data pequisada (*data do dia - 3*) o programa é interrompido
<br></br>
Para cada pagina iterada é feito o *scrape* da __*data da apresentação da proposição*__, do __*título*__(ou nome)__*da proposição*__ e __*id da proposição*__. 
<br></br>
O id da proposição é passado no link de cada proposição `  f'https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={id_preposicao}'  `
<br></br>
É feito um request nesse link e no __html__ de resposta encontramos o link do nosso documento alvo, o __PDF de Inteiro Teor__. 
<br></br>
O download do __PDF de Inteiro Teor__ é feito em um arquivo temporário e é extraído o hash MD5 desse arquivo. 
<br></br>
É feito um __yield__ com os itens  → **data de apresentação, título da proposição, id da proposição e md5**.

```
    def sigalei_crawler(self, response):
        resp_json = json.loads(response.body)
        i = 0
        for data_limite in resp_json['hits']['hits']:
            data_limite_compara = data_limite['_source']['dataApresentacao'][:10]
            data_limite_compara = datetime.strptime(data_limite_compara, '%Y-%m-%d').date()
            titulo = resp_json['hits']['hits'][i]['_source']['titulo'].replace('/', '-')
            id_preposicao = resp_json['hits']['hits'][i]['_id']
            i += 1
            if data_limite_compara >= self.dias_3:
                url_prep = f'https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={id_preposicao}'
                resp = requests.get(url=url_prep)
                tree = html.fromstring(html=resp.text)
                link_pdf = tree.xpath('//*[@id="content"]/h3[1]/span[2]/a/@href')[0]
                elo = link_pdf[link_pdf.find('codteor'):]
                url_pdf = f'https://www.camara.leg.br/proposicoesWeb/prop_mostrarintegra?{elo}.pdf'
                chunk_size = 2000
                r = requests.get(url_pdf, stream=True)
                salva_pdf = 'salva_pdf'
                with open(f'{salva_pdf}.pdf', 'wb') as fd:
                    for chunk in r.iter_content(chunk_size):
                        fd.write(chunk)
                path = f'{salva_pdf}.pdf'
                with open(path, 'rb') as opened_file:
                    content = opened_file.read()
                    md5 = hashlib.md5()
                    md5.update(content)
                    md5_pdf = md5.hexdigest()
                yield {
                    'data': data_limite_compara.strftime('%Y-%m-%d'),
                    'projeto': titulo,
                    'index_projeto': id_preposicao,
                    'md5': str(md5_pdf)
                }
            else:
                break
```
***
## :arrow_forward:  Arquivo - pipelines.py

É criada uam tabela em *SQLite* onde são gravados os dados

## * open_spider()

A conexão com o banco é criada e a criação da tabela é executada.

```
    def open_spider(self, spider):
        self.connection = sqlite3.connect("sigalei.db")
        self.c = self.connection.cursor()
        try:
            self.c.execute('''
                CREATE TABLE IF NOT EXISTS sigalei(
                    data TEXT,
                    projeto TEXT,
                    index_projeto PRIMARY KEY,
                    md5 TEXT
                )
            ''')
            self.connection.commit()
        except sqlite3.OperationalError:
            pass
```

***

## * close_spider()

O arquivo em pdf que é salvo temporariamente para realizar o *hash md5* é deletado e na sequencia é fechada a conexão com o banco.

A conexão com o banco é criada e a criação da tabela é executada.

```
    def close_spider(self, spider):
        try:
            salva_pdf = 'salva_pdf'
            path = f'{salva_pdf}.pdf'
            os.remove(path)
        except:
            pass
        self.connection.close()
```

***

## * process_item()

É executada a inserção dos itens no banco de dados.

```
    def process_item(self, item, spider):
        self.c.execute('''
            INSERT OR IGNORE INTO sigalei (data,projeto,index_projeto,md5) VALUES(?,?,?,?)

        ''', (
            item.get('data'),
            item.get('projeto'),
            item.get('index_projeto'),
            item.get('md5')
        ))
        self.connection.commit()
        return item
```
