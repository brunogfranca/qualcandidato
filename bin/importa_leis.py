# -*- coding: utf-8 -*-
import sys, re
import urllib2
from datetime import datetime, timedelta
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
leis = MongoClient(**mongoconfig).leis.leis

tidy_options = {
    'show-warnings': False
}


def carrega_dados_lei(lei):
    response = urllib2.urlopen(lei.get('url'))
    html, errors = tidy_document(response.read(), tidy_options)
    if errors:
        sys.exit(errors)
    parsed_html = BeautifulSoup(html)

    titulo = parsed_html.find('h4').text.strip()
    descricao = parsed_html.find('td', attrs={'id':'prim_col'}).text.strip()
    dados = {
        'titulo_completo': titulo,
        'descricao': descricao
    }
    if lei.has_key('voto'):
        del(lei['voto'])
    lei.update(dados)
    return lei


def salvar_dados(dados):
    leis.insert(dados)
    return leis.find_one(dados)


def carrega_leis():
    # DEBUG
    count = 0
    x = datetime.now()
    print x
    # /DEBUG
    result = politicos.find({'votos':{'$ne':[]}})
    for politico in result:
        lista_votos = []
        for lei in politico.get('votos', []):
            # DEBUG
            count += 1
            sys.stdout.write("\r%s" %(count))
            sys.stdout.flush()
            # /DEBUG
            if not lei.get('url'):
                continue
            
            lei_obj = leis.find_one({'url':lei.get('url')})
            if not lei_obj:
                dados = carrega_dados_lei(lei)
                lei_obj = salvar_dados(dados)
            
            lei.update(lei_obj)
            if lei.has_key('_id'):
                del(lei['_id'])
            lista_votos.append(lei)

        politicos.update({'idx':politico.get('idx')}, {'$set':{
            'votos':lista_votos
        }})
    # DEBUG
    y = datetime.now()
    print y
    print y - x
    # /DEBUG

carrega_leis()