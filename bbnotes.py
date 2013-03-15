from webapp_cached import CachedRequestHandler
import fetcher
from versions import version_ok 
from manifest import Manifest
import logging
from stringtables import get_stringtables_entities
import re
from google.appengine.api import urlfetch,memcache

hon_colors = ["00","1C","38","54","70","8C","A8","C4","E0","FF"]

def isDigit(c):
    return c in ['0','1','2','3','4','5','6','7','8','9']

custom_colors = { '970' : '#ffcc00' , '079' : 'DeepSkyBlue' , '717' : 'DarkOrchid',
        '292' : 'Lime' }

re_smilie = re.compile(r'<div[^>]+class="tr">.+?<div[^>]+class="[^"]*smilietext[^"]*"[^>]*>([^<]+).+?<div[^>]+class="[^"]*smiliedesc[^"]*"[^>]*>([^<]+)',flags=re.DOTALL)
def fetch_honsmilies():
    smilies = memcache.get('honforumsmilies')
    if smilies: return smilies
    result = urlfetch.fetch('http://forums.heroesofnewerth.com/misc.php?do=showsmilies',deadline=10)
    smilies = ('',{})
    names = []
    for m in re_smilie.finditer(result.content):
        name = m.group(2).lower()
        value = m.group(1)
        if name in smilies[1] and smilies[1][name][-2] not in '1234567890':
            continue
        elif name == 'mad':
            break
        smilies[1][name] = value
        names.append(name)
        if name.startswith('the '):
            name = name[4:]
            smilies[1][name] = value
            names.append(name)
    names.append('bottle')
    smilies[1]['bottle'] = ':bottle:'
    smilies = (re.compile(r'^(\ *(?:\[[^\]]+\])?)(%s)' % ('|'.join(names)),flags = re.IGNORECASE | re.MULTILINE),smilies[1])
    memcache.set('honforumsmilies',smilies)
    return smilies
def hon2html(msg):
    white = True
    parts = msg.split('^')
    msg = parts[0]
    for part in parts[1:]:
        if len(part) < 1:
            msg += '^'
        elif part[0] == 'w' or part[0] == 'W' or part[0] == '*':
            if not white:
                msg += '[/color]'
            msg += part[1:]
            white = True
        elif part[0] == 'r' or part[0] == 'R':
            if not white:
                msg += '[/color]'
            msg += '[color=#FF4C4C]' + part[1:]
            white = False
        elif part[0] == 'y' or part[0] == 'Y':
            if not white:
                msg += '[/color]'
            msg += '[color=#FFFF19]' + part[1:]
            white = False
        elif part[0] == 'g' or part[0] == 'G':
            if not white:
                msg += '[/color]'
            msg += '[color=#008000]' + part[1:]
            white = False
        elif part[0] == 'k' or part[0] == 'K':
            if not white:
                msg += '[/color]'
            msg += '[color=#000000]' + part[1:]
            white = False
        elif part[0] == 'c' or part[0] == 'C':
            if not white:
                msg += '[/color]'
            msg += '[color=#00FFFF]' + part[1:]
            white = False
        elif part[0] == 'b' or part[0] == 'B':
            if not white:
                msg += '[/color]'
            msg += '[color=#4C4CFF]' + part[1:]
            white = False
        elif part[0] == 'm' or part[0] == 'M':
            if not white:
                msg += '[/color]'
            msg += '[color=#FF00FF]' + part[1:]
            white = False
        elif len(part) >= 3 and isDigit(part[0]) and isDigit(part[1]) and isDigit(part[2]):
            if part[0:3] in custom_colors:
                color = custom_colors[part[0:3]]
            else:
                color = '#%s%s%s' % (hon_colors[int(part[0])],hon_colors[int(part[1])],hon_colors[int(part[2])])
            msg += '[color=%s]' % (color)  + part[3:]
            white = False
    if not white: msg += '[/color]'
    return msg

ver_sub = re.compile(r'^(\ *(?:\[[^\]]+\])?)(Version\ +(?:[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?))',flags=re.MULTILINE)
head_sub = re.compile(r'^(\ *(?:\[[^\]]+\])?)\=\=([^=]+)\=\=',flags=re.MULTILINE)
hr_sub = re.compile(r'^-+$',flags=re.MULTILINE)
class  BBNotes(CachedRequestHandler):
    redirect_latest = True
    def get_page(self,arch,version):
        manifest = fetcher.fetch(arch,version,'manifest.xml')
        if manifest is not None:
            version_ok(arch,version)
        else:
            self.response.out.write("Sorry, could not fetch manifest for {0} version".format(version))
            return
        manifest = Manifest(manifest)
        data = fetcher.fetch(arch,fetcher.normalize_ver(manifest.files['change_log_color.txt']['version']),'change_log_color.txt')
        if data is None: return
        data = data.read()
        try:
            data = data.decode('utf8')
        except:
            data = data.decode('cp1251')
        data = data.replace('\r\n','\n')
        data = hon2html(data)
        data = re.sub(ver_sub,r'\1[color=Yellow][SIZE=6][b]\2[/b][/size][/color]',data)
        data = re.sub(head_sub,r'\1[B]==[SIZE=4]\2[/size]==[/b]',data)
        data = re.sub(hr_sub,r'[hr][/hr]',data)
        smilies = fetch_honsmilies()
        data = re.sub(smilies[0],lambda m: '%s%s  [b]%s[/b]' % (m.group(1), smilies[1][m.group(2).lower()], m.group(2)),data)
        return ''.join(['<pre>',data,'</pre>'])

