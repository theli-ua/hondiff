from webapp_cached import CachedRequestHandler
from google.appengine.ext import db
from google.appengine.api import taskqueue
import templates
from versions import version_ok 
from world import Node,Index
from versions import Version,get_versions
from stringtables import get_stringtables_entities
from manifest import Manifest
import fetcher
import logging

class  HoNHero(CachedRequestHandler):
    redirect_latest = True
    def get_page(self,arch,version,hero):
        v = Version.get_by_key_name(version)
        if arch != fetcher.ARCHS.LINUX_RETAIL:
            return '<pre>Sorry, DB is disabled for RCT/SBT</pre>'
        elif v is None or not v.imported:
            versions = get_versions()
            versions.sort(key = lambda x: [int(y) for y in x.split('.')])
            if version == versions[-1]:
                self.response.out.write("Sorry, this version is not imported into db yet, importing was put into queue")
                taskqueue.add(url='/import',params={'version' : version,'arch' : arch},queue_name='importer')
            else:
                self.redirect('/query/latest/?' + self.request.query_string)
            return None
        else:
            if hero is None:
                manifest = fetcher.fetch(arch,version,'manifest.xml')
                manifest = Manifest(manifest)
                query = "Select * from Node where tag='hero'".format(version)
                q = db.GqlQuery(query)
                result = q.fetch(1000)
                for hero in result:
                    if hasattr(hero,'attackprojectile') and hero.attackprojectile != '':
                        hero.projectilespeed = db.GqlQuery("Select * from Node where name='{0}'".format(hero.attackprojectile)).fetch(1)[0].speed
                    else:
                        hero.projectilespeed = '""'

                    #get url for icon
                    icon = hero.icon.replace('.tga','.dds')
                    path = '/'.join(hero.key().name().split('|')[1].split('/')[:-1])
                    path = '/'.join([path,icon])
                    path = path.replace('game/resources0.s2z','game/textures.s2z/00000000')
                    path = '/'.join([manifest.files[path]['version'],path])
                    hero.iconurl = path
                template_values = {}
                template_values['data'] = result
                template_values['stringtables'] = get_stringtables_entities(arch,version)
                template_name = self.request.get('template')
                if template_name and template_name == 'csv':
                    template = templates.get_template('heroes.csv')        
                else:
                    template = templates.get_template('heroes.html')        
                #self.response.out.write(template.render(template_values))
                #return None
                return template.render(template_values)
            else:
                hero = db.GqlQuery("Select * from Node where tag='hero' and name = :1",hero).fetch(1)
                if len(hero) == 0:
                    return 'Sorry, such hero is not found'
                hero = hero[0]
                #get url for icon
                manifest = fetcher.fetch(arch,version,'manifest.xml')
                manifest = Manifest(manifest)
                icon = hero.icon.replace('.tga','.dds')
                path = '/'.join(hero.key().name().split('|')[1].split('/')[:-1])
                path = '/'.join([path,icon])
                path = path.replace('game/resources0.s2z','game/textures.s2z/00000000')
                path = '/'.join([manifest.files[path]['version'],path])
                hero.iconurl = path
                abilities = db.GqlQuery("Select * from Node where tag='ability' and name in :1",[hero.inventory0,hero.inventory1,hero.inventory2,hero.inventory3]).fetch(10)
                for a in abilities:
                    icon = a.icon.replace('.tga','.dds')
                    path = '/'.join(a.key().name().split('|')[1].split('/')[:-1])
                    path = '/'.join([path,icon])
                    path = path.replace('game/resources0.s2z','game/textures.s2z/00000000')
                    path = '/'.join([manifest.files[path]['version'],path])
                    a.iconurl = path

                #abilities = dict([(a.name,a) for a in abilities])
                template_values = {}
                template_values['entity'] = hero
                template_values['version'] = version
                template_values['abilities'] = abilities
                template_values['stringtables'] = get_stringtables_entities(arch,version)
                template = templates.get_template('hero.html')        
                return template.render(template_values)
