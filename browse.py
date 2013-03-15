#!/usr/bin/env python
#
# Copyright 2011 Anton Romanov

from webapp_cached import CachedRequestHandler

import fetcher,templates

from versions import version_ok 
from manifest import Manifest
from filetypes import get_lang

class  HoNFileBrowser(CachedRequestHandler):
    redirect_latest = True
    def get_page(self,arch,version,path,fpath):
        manifest = fetcher.fetch(arch,version,'manifest.xml')
        if manifest is not None:
            #Version(value=version,key_name=version).put()
            version_ok(arch,version)
        else:
            self.response.out.write("Sorry, could not fetch manifest for {0} version".format(version))
            return
        manifest = Manifest(manifest)
        path = path[1:]
        if fpath != '':
            print 'file requested!'
        else:
            if path == '':
                nodes = manifest.files.keys()
            else:
                l = len(path)
                nodes = [f[l:] for f in manifest.files.keys() if f.startswith(path)]
            dirs = []
            files = []
            for x in nodes:
                n = x.split('/')
                if len(n) == 1:
                    x = path + x
                    f = { 'path' : n[0] , 'version' : fetcher.normalize_ver(manifest.files[x]['version']), 'size' : manifest.files[x]['size'] }
                    f['lang'] = get_lang(n[0])
                    f['fullpath'] = x
                    files.append(f)
                else:
                    dirs.append(n[0])
            dirs = frozenset(dirs)

            if path != '':
                up_url = '..'
            else:
                up_url = ''

            template_values = {
                    'version': version,
                    'path': path,
                    'dirs': sorted(list(dirs)),
                    'files' : files,
                    'up_url' : up_url,
                    'base_url' : fetcher.get_base_url(arch),
                    'base_url2' : fetcher.get_base_url2(arch),
                    }
            template = templates.get_template('folder.html')
            return template.render(template_values)



