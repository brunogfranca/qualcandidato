# -*- coding: utf-8 -*-
import sys, re
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup
from tidylib import tidy_document
from redisconf.config import Config
from pymongo import MongoClient


conf = Config('excelencias')
env = conf.getEnvironmentConfig()

# Conexão MongoDB
mongoconfig = {
    'host': env['mongodb_host'],
    'port': int(env['mongodb_port'])
}
if env['mongodb_replicaset']:
    mongoconfig['w'] = 2
    mongoconfig['replicaSet'] = env['mongodb_replicaset']

politicos = MongoClient(**mongoconfig).politicos.politicos

tidy_options = {
    'show-warnings': False
}

def carrega_dados_politico(idx):
    response = urllib2.urlopen('http://www.excelencias.org.br/@parl.php?id=%s'%idx)
    html, errors = tidy_document(response.read(), tidy_options)
    if errors:
        sys.exit(errors)
    parsed_html = BeautifulSoup(html)

    conteudo = parsed_html.body.find('div', attrs={'id':'conteudo'}).find_all('div', attrs={'id':'contem_parl'})
    if len(conteudo) <= 4:
        return

    bloco_principal = conteudo[0]
    bloco_votacoes = None
    for bloco in conteudo:
        if bloco.find('div', attrs={'id':'contem_titulo_parl'}).text.strip() == u'Como votou matérias no Plenário':
            bloco_votacoes = bloco
    if not bloco_votacoes:
        return

    nome = bloco_principal.find('div', attrs={'id':'contem_titulo_parl'}).text.strip()
    if not nome:
        return
    tabela_votacoes = bloco_votacoes.find('table', attrs={'class':'livre'})

    lista_votos = []
    if tabela_votacoes:
        for linha in tabela_votacoes.find_all('tr'):
            titulo_lei = linha.find('td', attrs={'id':'prim_col'}).text.strip()
            voto = linha.find('td', attrs={'class':'esq'}).text.strip()
            link_lei = linha.find('td', attrs={'id':'prim_col'}).find('a')
            url_lei = ''
            if link_lei:
                cod, num, ano, casa = link_lei.get('href').replace('javascript:parent.traz_pl(', '').split(',')
                url_lei = 'http://www.excelencias.org.br/modulos/parl_projetolei.php?cod=%s&num=%s&ano=%s&casa=%s'
                url_lei = url_lei %(cod.replace("'", ''), num, ano, casa.replace(')', ''))

            lista_votos.append({
                'titulo': titulo_lei,
                'voto': voto,
                'url': url_lei
            })
    dados_politico = {
        'idx': int(idx),
        'nome': nome,
        'votos': lista_votos
    }
    return dados_politico


def salvar_dados(dados):
    politicos.insert(dados)


def popula_dados():
    # DEBUG
    count = 0
    x = datetime.now()
    print x
    # /DEBUG
    ultimo_idx = politicos.find_one(sort=[('idx', -1)],limit=1)
    if ultimo_idx:
        ultimo_idx = ultimo_idx.get('idx', 1)
    else:
        ultimo_idx = 1
    total = len(range(ultimo_idx,80000))
    for i in range(ultimo_idx,80000):
        politico = politicos.find_one({'idx':i})
        if not politico:
            dados = carrega_dados_politico(i)
            if not dados:
                continue
            salvar_dados(dados)
        # DEBUG
        if count % 1 == 0:
            percent = (float(count) / total) * 100.0
            z = datetime.now()
            delta = z-x
            timestamp_delta = delta.total_seconds()
            if percent > 5:
                eta_secs = (100.0/percent)*timestamp_delta
                eta = timedelta(seconds=eta_secs-timestamp_delta)
            else:
                eta = '--CALCULANDO--'
            sys.stdout.write("\r%d%% - %s - ETA %s - %s" %(percent, delta, eta, i))
            sys.stdout.flush()
        count += 1
        # /DEBUG

popula_dados()