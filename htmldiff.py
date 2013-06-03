#!/usr/bin/env python
#
# Copyright 2011 Anton Romanov
from webapp_cached import CachedRequestHandler
import fetcher
from difflib import unified_diff,HtmlDiff


from cgi import escape
import templates
import logging


from versions import version_ok, version_arch
from manifest import Manifest
from filetypes import is_diffable
htmldiff = HtmlDiff()

class Changeset:
    def __init__(self,s,d):
        oldset = frozenset(s.files.keys())
        newset = frozenset(d.files.keys())
        self.dels = oldset - newset
        self.adds = newset - oldset
        self.changes = frozenset([x for x in list(oldset & newset) if \
                s.files[x]['checksum']!= d.files[x]['checksum']])
                #s.files[x]['version'] != d.files[x]['version'] or \

class  HoNhtmldiff(CachedRequestHandler):
    def ChangeSet(self,arch,source_version,target_version):
        out = ''
        arches = self.request.get('arches')
        if arches:
            oarch,narch = (int(_) for _ in arches.split('|')[:2])
        else:
            oarch = version_arch(source_version)
            narch = version_arch(target_version)

        if oarch is None: oarch = arch
        if narch is None: narch = arch

        omanifest = fetcher.fetch(oarch,source_version,'manifest.xml')
        nmanifest = fetcher.fetch(narch,target_version,'manifest.xml')


        if omanifest is not None:
            #Version(value=source_version,key_name=source_version).put()
            version_ok(oarch,source_version)
        if nmanifest is not None:
            #Version(value=target_version,key_name=target_version).put()
            version_ok(narch,target_version)            
        if omanifest is None:
            out += ('Sorry, could not fetch manifest for %s' % source_version)
        elif nmanifest is None:
            out += ('Sorry, could not fetch manifest for %s' % target_version)
        else:
            omanifest = Manifest(omanifest)
            nmanifest = Manifest(nmanifest)

            changeset = Changeset(omanifest,nmanifest)

            changes = ( {'path' : f, 'old_version' : omanifest.files[f]['version'], \
                    'new_version' : nmanifest.files[f]['version'] } for f in changeset.changes )
            adds = ( {'path' : f,  \
                    'new_version' : nmanifest.files[f]['version'] } for f in changeset.adds )
            dels = ( {'path' : f, 'old_version' : omanifest.files[f]['version']\
                     } for f in changeset.dels )

            template_values = {
                    'source_version': source_version,
                    'target_version': target_version,
                    'changes': changes,
                    'adds' : adds,
                    'dels' : dels,
                    'base_url' : fetcher.get_base_url(arch),
                    'base_url2' : fetcher.get_base_url(arch, 1),
                    'arches' : '|'.join([str(_) for _ in [oarch,narch]]),
                    }
            template = templates.get_template('changeset.html')
            return template.render(template_values)
        self.response.out.write(out)
        return None



    def get_page(self,arch,source_version,target_version,path):
        if path == '' or path == '/':
            return self.ChangeSet(arch,source_version,target_version)
        out = ''
        diffable = is_diffable(path)

        if not diffable:
            return 'Sorry, this file is not diffable'
        arches = self.request.get('arches')
        if arches:
            oarch,narch = (int(_) for _ in arches.split('|')[:2])
        else:
            oarch = version_arch(source_version)
            narch = version_arch(target_version)
        odata = fetcher.fetch(oarch,source_version,path)
        ndata = fetcher.fetch(narch,target_version,path)
        if odata is None:
            out += ('Sorry, could not fetch file %s for version %s.<br>' % \
                    (source_version,path))
        elif ndata is None:
            out += ('Sorry, could not fetch file %s for version %s.<br>' % \
                    (target_version,path))
        else:
            odata = odata.read()
            ndata = ndata.read()
            try:
                odata = odata.decode('utf8')
            except:
                odata = odata.decode('cp1251')

            try:
                ndata = ndata.decode('utf8')
            except:
                ndata = ndata.decode('cp1251')
            #return htmldiff.make_table(odata.splitlines(),ndata.splitlines())

            out += ('<div class="unified_diff">')
            out += ("<pre>")
            diff = unified_diff(odata.splitlines(),ndata.splitlines(),fromfile=source_version,tofile=target_version)
            prevdiv = ' '
            divs = { ' ' : '', '+' : 'add' , '-' : 'del' , '@' : 'linenum'}
            curdiv = ''
            for l in diff:
                line = escape(l)
                curdiv = line[0]

                if curdiv != prevdiv:
                    if prevdiv != ' ':
                        out += ('</div>')
                    if curdiv != ' ':
                        out += ('<div class="%s">' % divs[curdiv])
                out += (escape(l))
                out += ("\n")
                prevdiv = curdiv
            if curdiv != ' ':
                out += ('</div>')
            out += ("</div>")
            out += ("\n</pre>")
        return out

