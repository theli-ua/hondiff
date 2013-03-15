from google.appengine.ext import db
import fetcher
from lxml import etree
from versions import Version,version_ok
from manifest import Manifest
from google.appengine.ext import webapp
import logging
import re

split_re = re.compile('[\ ,]')

#class Entity(db.Expando):
    #entitytype = db.StringProperty()
    #version = db.ListProperty()
    #fileversion = db.StringProperty()
    #let the key be  fileversion|filepath
class AllowedAccess(db.Model):
    rct = db.BooleanProperty(indexed=False)
    sbt = db.BooleanProperty(indexed=False)

class Index(db.Model):
    data = db.TextProperty()

class StoredQuery(db.Model):
    query = db.TextProperty()
    keywords = db.TextProperty()

class Node(db.Expando):
    tag = db.StringProperty()
    entitytype = db.StringProperty()
    #pure = db.BooleanProperty()
    def get_root(self):
        root = self
        while root.parent() is not None:
            root = root.parent()
        return root
    def get_root_path(self):
        current = self
        path = [current]
        while current.parent() is not None:
            current = current.parent()
            path.append(current)
        return path

def checknum(value):
    try:
        if value.isdigit():
            return float(value)
        elif value[0] == '-' and value[1:].isdigit():
            return -float(value[1:])
        return float(value)
    except:
        return value

def parse_attrib(a):
    a = dict(a)
    for n in a:
        if isinstance(a[n],str):
            #logging.info(n)
            #logging.info(a[n])
            #v = a[n].split(',')
            v = split_re.split(a[n])
            if len(v) > 1:
                for i in xrange(len(v)):
                    v[i] = checknum(v[i])
                a[n] = v
            else:
                a[n] = checknum(v[0])
            if n == 'key':
                a['Key'] = a[n]
                del a[n]
    return a
        
def parse_node(n,parent_entity):
    node = Node(parent=parent_entity,key_name=None,tag=n.tag,\
            entitytype=parent_entity.entitytype,\
            versions=parent_entity.versions,**parse_attrib(n.attrib))
    node.put()
    for x in n:
        parse_node(x,node)

def parse_entity(xml,version,path,versions=None):
    try:
        root = etree.parse(xml,parser=etree.ETCompatXMLParser()).getroot()
    except:
        logging.error('Failed to parse %s, skipping' % path)
        return
    pure = path.startswith('game/resources0.s2z')
    if not pure:
        return
    entity = Node(key_name='|'.join([version,path]), tag=root.tag, entitytype=root.tag, **parse_attrib(root.attrib))
    if versions is not None:
        entity.versions = versions
    entity.put()
    for n in root:
        parse_node(n,entity)

def set_version(e,version):
    children = db.Query()
    children.ancestor(e)
    for c in children:
        c.versions += [version]
        c.put()

def delete_group(e):
    children = db.Query()
    children.ancestor(e)
    for c in children:
        c.delete()

def import_manifest(arch,version):
    v = Version.get_by_key_name(version)
    if v is None or not v.imported:
        m = fetcher.fetch(arch,version,'manifest.xml')
        if m is not None:
            m = Manifest(m)
            #xg_on = db.create_transaction_options(xg=True)
            v = version_ok(arch,version)
            prev = db.GqlQuery('select * from Version where imported = True and arch = {0}'.format(arch)).fetch(1)
            if prev is not None and len(prev) > 0:
                prev = prev[0]
                from htmldiff import Changeset
                pmanifest = Manifest(fetcher.fetch(arch,prev.value,'manifest.xml'))
                changes = Changeset(pmanifest,m)
                to_delete = [ pmanifest.files[x] for x in changes.dels | changes.changes 
                        if pmanifest.files[x]['path'].endswith('entity') and pmanifest.files[x]['path'].startswith('game/resources0.s2z')]
                to_import = [ m.files[x] for x in changes.adds | changes.changes if 
                        m.files[x]['path'].endswith('entity') and m.files[x]['path'].startswith('game/resources0.s2z')]
                total = len(to_delete)
                current = 1
                del(changes)
                del(m)
                del(pmanifest)
                for file in to_delete:
                    e = Node.get_by_key_name('|'.join([file['version'],file['path']]))
                    if e is not None:
                        logging.info('[{1}/{2}] Deleting {0} entity group'.format('|'.join([file['version'],file['path']]),current,total))
                        db.run_in_transaction(delete_group,e)
                    current += 1
                del(to_delete)
            else:
                prev = None
                to_import = [x for x in m.files.values() if x['path'].endswith('entity') and x['path'].startswith('game/resources0.s2z')]
            
            total = len(to_import)
            current = 1
            for file in to_import:
                if file['path'].endswith('.entity'):
                    e = Node.get_by_key_name('|'.join([file['version'],file['path']]))
                    if e is None:
                        data = fetcher.fetch(arch,file['version'],file['path'])
                        #if data is None:
                            #continue
                        logging.info('[%d/%d] importing %s %s into db' % (current,total,file['version'],file['path']))
                        db.run_in_transaction(parse_entity,data,file['version'],file['path'],[version])
                        #db.run_in_transaction_options(xg_on,parse_entity,file['version'],file['path'],[version])
                    #elif version not in e.versions:
                        #db.run_in_transaction(set_version,e,version)
                current += 1
            v.imported = True
            v.put()
            if prev is not None:
                prev.imported = False
                prev.put()

class ImportWorker(webapp.RequestHandler):
    def post(self):
        version = self.request.get('version')
        arch = int(self.request.get('arch'))
        import_manifest(arch,version)

