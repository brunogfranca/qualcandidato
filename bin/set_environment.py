#! /usr/bin/env python
# -*- coding: utf-8 -*-

from redisconf.config import Config

conf = Config('excelencias')

questions = []

# MongoDB
questions.append({'key':'mongodb_host','question':"mongodb's host (or primary instance)", 'default':'127.0.0.1'})
questions.append({'key':'mongodb_port','question':"mongodb's port", 'default':27017})
questions.append({'key':'mongodb_replicaset','question':"mongodb's replica set"})

conf.configureEnvironment(questions)