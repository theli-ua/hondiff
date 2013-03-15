#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
#from google.appengine.ext.webapp import util
from htmldiff import HoNhtmldiff
from browse import HoNFileBrowser
from highlight import HoNFileViewer
from world import ImportWorker
from query import HoNQuery
from heroes import HoNHero
from texture import HoNTexture
from gamelog import GameLogRedirector
from bbnotes import BBNotes
from fetcher import ARCHS
#from google.appengine.ext.webapp import template
import os
from versions import get_versions
import templates
class MainHandler(webapp2.RequestHandler):
    def get(self):
        arch = ARCHS.LINUX_RETAIL
        arches = self.request.get('arches')
        if arches :
            arch = sorted([int(_) for _ in arches.split('|')])[-1]
        elif self.request.headers['Host'].split('.')[0] == 'rct':
            arch = ARCHS.LINUX_RCT
        elif self.request.headers['Host'].split('.')[0] == 'sbt':
            arch = ARCHS.LINUX_SBT
        #self.response.out.write('Hello world!')
        versions = get_versions(arch)
        versions.sort(key = lambda x: [int(y) for y in x.split('.')])
        version = versions[-1]
        prevversion = versions[-2]
        template_values = {
            'versions' : get_versions(),
            'latest' : version,
            'previous' : prevversion,
            }
        template = templates.get_template('index.html')        
        self.response.out.write(template.render(template_values))


class RedirectHandler(webapp2.RequestHandler):
    def get(self,path):
        newurl = 'hondifftmphosting.appspot.com'
        if self.request.headers['Host'].split('.')[0] == 'rct':
            newurl = 'rct.' + newurl
        elif self.request.headers['Host'].split('.')[0] == 'sbt':
            newurl = 'sbt.' + newurl
        if len(self.request.query_string) > 0:
            self.redirect("http://" + newurl + "/" + path + '?' + self.request.query_string)
        else:
            self.redirect("http://" + newurl + "/" + path)

application = webapp2.WSGIApplication([
        #('/(.*)', RedirectHandler),
        ('/', MainHandler),
        ('/htmldiff/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)(/?.*)',HoNhtmldiff),
        ('/browse/((?:[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)|latest)(/.*?)([^/]*)', HoNFileBrowser),
        ('/highlight/([0-9\.]+?)(/.+?)', HoNFileViewer),
        ('/import',ImportWorker),
        ('/query/((?:[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)|latest)/?', HoNQuery),
        ('/bbnotes/((?:[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)|latest)/?', BBNotes),
        ('/heroes/((?:[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)|latest)/?([a-zA-Z_0-9]+?)?', HoNHero),
        ('/texture/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/(.*)', HoNTexture),
        ('/gamelog/([0-9]+)', GameLogRedirector),
        ],debug=False)


