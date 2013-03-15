
#!/usr/bin/env python
#
# Copyright 2011 Anton Romanov

from google.appengine.ext import db
from webapp_cached import CachedRequestHandler
from google.appengine.api import datastore_errors
from google.appengine.api import taskqueue
from stringtables import get_stringtables_entities

import logging
import urllib

import templates

from versions import get_versions
from world import StoredQuery
from versions import Version
from fetcher import ARCHS

class  HoNQuery(CachedRequestHandler):
    redirect_latest = True
    def post(self,version):
        query = self.request.get('query')
        query = urllib.unquote(query)
        keywords = self.request.get('keywords')
        stored = StoredQuery(query=query,keywords=keywords)
        self.redirect(self.request.url + '?stored_query=' + str(stored.put()))
    def get_page(self,arch,version):
        error = ''
        query = ''
        keywords = ''
        stored_key = self.request.get('stored_query')
        if stored_key:
            try:
                stored = StoredQuery.get(stored_key)
                if not stored:
                    error = 'Sorry, there was no such stored query'
                else:
                    query = stored.query
                    keywords = stored.keywords
            except:
                error = 'Sorry, there was no such stored query'
        else:
            query = self.request.get('query')
            query = urllib.unquote(query)
            keywords = self.request.get('keywords')

        template_values = {
            'query' : query,
            'version' : version,
            }

        query = query.strip()
        data = []

        v = Version.get_by_key_name(version)
        if arch != ARCHS.LINUX_RETAIL:
            return '<pre>Sorry, DB is disabled for RCT/SBT</pre>'
        if v is None or not v.imported:
            versions = get_versions(arch)
            versions.sort(key = lambda x: [int(y) for y in x.split('.')])
            if version == versions[-1]:
                error = "Sorry, this version is not imported into db yet, importing was put into queue"
                taskqueue.add(url='/import',params={'version' : version,'arch' : arch},queue_name='importer')
            else:
                self.redirect('/query/latest/?' + self.request.query_string)
        else:
            if len(query) > 0:
                for qline in query.splitlines():
                    operation = ''
                    if qline[0] == '&':
                        operation = '&'
                        qline = qline[1:]
                    elif qline[0] == '!':
                        operation = '!'
                        qline = qline[1:]
                    try:
                        qline = "Select * from Node where {0}".format(qline)
                        logging.info(qline)
                        q = db.GqlQuery(qline)
                    except:
                        error = 'Sorry this query was malformed'
                        q = None
                    if q is not None:
                        pb = q._proto_query
                        inequalities = {}
                        for k,v in pb.filters().iteritems():
                            #keywords.append(k[0])
                            if k[1] == '!=':
                                inequalities[k[0]] = set([v[1][0]._Literal__value for v in v])
                        #logging.info(inequalities)
                        #for k in pb.orderings():
                            #keywords.append(k[0])
                        if len(pb.orderings()) > 0:
                            error = 'Sorry order by is not allowed'
                        else:

                            try:
                                result = q.fetch(1000)
                                #logging.info('results: {0}'.format(len(result)))
                                _result = []
                                for r in result:
                                    ok = True
                                    for prop,keys in inequalities.iteritems():
                                        l = getattr(r,prop)
                                        if isinstance(l,list):
                                            l = set(l)
                                        else:
                                            l = set([l])
                                        if len(l & keys) > 0:
                                            ok = False
                                            #logging.info('filtered')
                                            #logging.info(l)
                                            break
                                        if not ok: break
                                    if ok:
                                        _result.append(r)
                                result = _result
                                _data = []
                                for node in result:
                                    root = node
                                    while root.parent() is not None:
                                        root = root.parent()
                                    _data.append((root.key().name(),root,node))
                                if operation == '&':
                                    roots = set([x[0] for x in _data])
                                    _data = [x for x in data if x[0] in roots]
                                    data = _data
                                elif operation == '!':
                                    roots = [x[0] for x in _data]
                                    _data = [x for x in data if x[0] not in roots]
                                    data = _data
                                else:
                                    data.extend(_data)

                            except datastore_errors.NeedIndexError, exc:
                                x = str(exc)
                                error = 'Sorry, this query is not possible without additional indices'

        template_values['data'] = data
        if len(keywords.strip()) > 0:
            template_values['keywords'] = keywords.split(',')
            numbers = []
            for k in template_values['keywords']:
                for r in data:
                    r = r[2]
                    if hasattr(r,k) and getattr(r,k) != '':
                        if isinstance(getattr(r,k),float):
                            numbers.append(k)
                        break
            template_values['numbers'] = numbers
        else:
            template_values['keywords'] = []
            template_values['numbers'] = []
        template_values['stringtables'] = get_stringtables_entities(arch,version)
        template_values['error'] = error
        template = templates.get_template('query.html')        
        if error == '':
            return template.render(template_values)
        else:
            self.response.out.write(template.render(template_values))
            return None
