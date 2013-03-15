#!/usr/bin/env python
from google.appengine.ext import webapp
from google.appengine.api import urlfetch


class GameLogRedirector(webapp.RequestHandler):
    def get(self,matchid):
        resp = urlfetch.fetch(url='http://replaydl.heroesofnewerth.com/replay_dl.php?file=&match_id=' + matchid, follow_redirects=False)
        if resp.status_code == 302:
            self.redirect(resp.headers['location'][:-9] + 'zip')


