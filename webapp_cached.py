from google.appengine.ext import webapp
from versions import get_versions
import logging
from google.appengine.api import users
from world import AllowedAccess
from fetcher import ARCHS
from google.appengine.api.memcache import flush_all
import multicache as memcache

class CachedRequestHandler(webapp.RequestHandler):
    content_type = None
    redirect_latest = False
    def get(self,*args):
        arch = ARCHS.LINUX_RETAIL
        arches = self.request.get('arches')
        if arches :
            arch = sorted([int(_) for _ in arches.split('|')])[-1]
        elif self.request.headers['Host'].split('.')[0] == 'rct':
            arch = ARCHS.LINUX_RCT
        elif self.request.headers['Host'].split('.')[0] == 'sbt':
            arch = ARCHS.LINUX_SBT

        if arch != ARCHS.LINUX_RETAIL:
            user = users.get_current_user()
            if user:
                u = AllowedAccess.get_by_key_name(user.email().lower())
                if user.email().endswith('@s2games.com') or\
                (arch == ARCHS.LINUX_RCT and u and u.rct) or\
                (arch == ARCHS.LINUX_SBT and u and u.sbt):
                    pass
                else:
                    self.response.out.write('gtfo %s' % user.email())
                    return
            else:
                self.redirect(users.create_login_url(self.request.url))
        if self.redirect_latest and args[0] == 'latest':
            versions = get_versions(arch)
            versions.sort(key = lambda x: [int(y) for y in x.split('.')])
            version = versions[-1]
            self.redirect(self.request.url.replace('latest',version).encode('utf8'))
        else:
            try:
                html = memcache.get(self.request.url)
            except:
                html = None
                flush_all()

            if html is None:
                html = self.get_page(arch,*args)
                #try:
                    #html = self.get_page(arch,*args)
                #except:
                    #html = 'Sorry, there was an error processing your request. Most probably hondiff is currently out of quota. App Engine resets all resource measurements at the beginning of each calendar day.'
                    #memcache.set(self.request.url,html,3600)
                try:
                    if html is not None:
                        memcache.set(self.request.url,html)
                except:
                    flush_all()
                    memcache.set(self.request.url,html)
            
            if html is not None:
                if self.content_type != None:
                    self.response.headers['Content-Type'] = self.content_type
                self.response.out.write(html)
