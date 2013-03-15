import webapp2
from google.appengine.api import urlfetch
from fetcher import OsArchTuple
from urllib import urlencode
from fetcher import ARCHS
from versions import version_ok

def unserialize(s):
    return _unserialize_var(s)[0]

def _unserialize_var(s):
    return (
        { 'i' : _unserialize_int
        , 'b' : _unserialize_bool
        , 'd' : _unserialize_double
        , 'n' : _unserialize_null
        , 's' : _unserialize_string
        , 'a' : _unserialize_array
        }[s[0].lower()](s[2:]))

def _unserialize_int(s):
    x = s.partition(';')
    return (int(x[0]), x[2])

def _unserialize_bool(s):
    x = s.partition(';')
    return (x[0] == '1', x[2])

def _unserialize_double(s):
    x = s.partition(';')
    return (float(x[0]), x[2])

def _unserialize_null(s):
    return (None, s)

def _unserialize_string(s):
    (l, _, s) = s.partition(':')
    return (s[1:int(l)+1], s[int(l)+3:])

def _unserialize_array(s):
    (l, _, s) = s.partition(':')
    a, k, s = {}, None, s[1:]

    for i in range(0, int(l) * 2):
        (v, s) = _unserialize_var(s)

        if k != None:
            a[k] = v
            k = None
        else:
            k = v
    return (a,s[1:])   

def getVerInfo(os,arch,masterserver,version = None, repair = False, current_version = None):
    details = {'version' : '0.0.0.0', 'os' : os ,'arch' : arch}
    if current_version is not None:
        details['current_version'] = current_version
    if version is not None:
        details['version'] = version
    if repair:
        details['repair'] = 1
    else:
        details['update'] = 1

    details = urlencode(details).encode('utf8')
    url = 'http://{0}/patcher/patcher.php'.format(masterserver)

    result = urlfetch.fetch(url=url,
                        payload=details,
                        method=urlfetch.POST,
                        headers={'Content-Type': 'application/x-www-form-urlencoded'})
    d = unserialize(result.content)
    return d

class VersionHandler(webapp2.RequestHandler):
    def get(self):
        retail = OsArchTuple.get_by_key_name('0')
        rct    = OsArchTuple.get_by_key_name('1')
        sbt    = OsArchTuple.get_by_key_name('2')
        try:
            version_ok(ARCHS.LINUX_RETAIL,getVerInfo(retail.os,retail.arch,'masterserver.hon.s2games.com')[0]['version'])
        except:pass
        try:
            version_ok(ARCHS.LINUX_RCT,getVerInfo(rct.os,rct.arch,'masterserver.hon.s2games.com')[0]['version'])
        except:pass
        try:
            version_ok(ARCHS.LINUX_SBT,getVerInfo(sbt.os,sbt.arch,'masterserver.hon.s2games.com')[0]['version'])
        except:pass

application = webapp2.WSGIApplication([
        ('/tasks/versions', VersionHandler),
        ],debug=False)
