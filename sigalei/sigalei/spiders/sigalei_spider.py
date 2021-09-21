import hashlib
from lxml import html
import requests
import scrapy
import json
from datetime import datetime, timedelta, date
from fake_useragent import UserAgent
from math import ceil


class SigaleiSpiderSpider(scrapy.Spider):
    name = 'sigalei_spider'
    allowed_domains = ['www.camara.leg.br']
    ano_atual = datetime.today().year
    hj = date.today()
    dias_3 = hj - timedelta(days=3)
    ua = UserAgent()
    headers = {
        'Content-Type': "application/json",
        'User-Agent': ua.random
    }

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
