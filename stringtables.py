from manifest import Manifest
import fetcher
import multicache as memcache
from google.appengine.api.memcache import flush_all
import re
re_entry = re.compile(r'(.+?)[\t\ ]+(.+)')

def get_stringtables_entities(arch,version):
    try:
        stringtable = memcache.get('stringtable|entities|{0}'.format(version))
    except:
        flush_all()
    if stringtable is not None:
        return stringtable
    stringtable = {}
    stringtable_version = Manifest(fetcher.fetch(arch,version,'manifest.xml')).files['game/resources0.s2z/stringtables/entities_en.str']['version']
    tabledata = fetcher.fetch(arch,stringtable_version,'game/resources0.s2z/stringtables/entities_en.str').read().decode('utf8')
    for line in tabledata.splitlines():
        m =  re_entry.match(line)
        if m:
            stringtable[m.group(1)] = m.group(2).strip()
    try:
        memcache.set('stringtable|entities|{0}'.format(version),stringtable)
    except:
        flush_all()
    return stringtable
