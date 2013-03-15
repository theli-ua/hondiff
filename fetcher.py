from __future__ import with_statement
from zipfile import ZipFile
from google.appengine.api import urlfetch
from StringIO import StringIO
from google.appengine.ext import blobstore
from google.appengine.api import files
from google.appengine.ext import db

global_url = 'http://patch.hon.s2games.com/'
global_url2  = 'http://dl.heroesofnewerth.com/'

class OsArchTuple(db.Model):
    os = db.TextProperty()
    arch = db.TextProperty()


class ARCHS:
    LINUX_RETAIL = 0
    LINUX_RCT  = 1
    LINUX_SBT  = 2


    #pfft, y u no wok
    #with OsArchTuple.get_by_key_name('0') as retail:#, OsArchTuple.get_by_key_name('1') as rct, OsArchTuple.get_by_key_name('2') as sbt:

    retail = OsArchTuple.get_by_key_name('0')
    rct    = OsArchTuple.get_by_key_name('1')
    sbt    = OsArchTuple.get_by_key_name('2')

    RETAIL_TUPLE = '/'.join([retail.os,retail.arch])
    RCT_TUPLE    = '/'.join([rct.os,rct.arch])
    SBT_TUPLE    = '/'.join([sbt.os,sbt.arch])

    del rct
    del sbt
    del retail

class FileEnt(db.Model):
    value = blobstore.BlobReferenceProperty(required=True)
    arch = db.IntegerProperty(default=ARCHS.LINUX_RETAIL)

def put_into_storage(key,data,arch):
    file_name = files.blobstore.create(mime_type='application/octet-stream')
    with files.open(file_name, 'a') as f:
        f.write(data)
    files.finalize(file_name)  
    image_blob_key = files.blobstore.get_blob_key(file_name)
    FileEnt(key_name=key,value=image_blob_key,arch=arch).put()

def get_from_storage(key,arch):
    blob =  FileEnt.get(db.Key.from_path('FileEnt', key))
    if blob is not None:
        if blob.arch <= arch:
            return blobstore.BlobReader(blob.value)
        else:
            return StringIO('')
    return None

def normalize_ver(version):
    if version.count('.') == 3 and version.endswith('.0'):
        version = version[:-2]
    return version

def get_base_url(arch, n = 0):
    if n == 0:
        url = global_url
    else:
        url = global_url2

    if arch == ARCHS.LINUX_RCT:
        return url + ARCHS.RCT
    elif arch == ARCHS.LINUX_SBT:
        return url + ARCHS.SBT_TUPLE
    else:
        return url + ARCHS.RETAIL_TUPLE 


def fetch(arch,version,path,save=True):
    version = normalize_ver(version)
    path = path.lstrip('/')
    key = 'zip%s%s' % (version,path)
    base_url = get_base_url(arch, 0)
    base_url2 = get_base_url(arch, 1)
    #zdata = memcache.get(key)
    path = path.replace(' ','%20')
    zdata = get_from_storage(key,arch)
    if zdata is None:
        result = urlfetch.fetch('%s/%s/%s.zip' % (base_url,version,path),deadline=10)
        #print result.status_code
        if result.status_code != 200:
            result = urlfetch.fetch('%s/%s/%s.zip' % (base_url2,version,path))
        if result.status_code == 200:
            zdata = result.content
            #memcache.set(key,zdata)
            if save:
                try:
                    put_into_storage(key,zdata,arch)
                except:pass
            zdata = StringIO(zdata)
    if zdata is None:
        return None
    #zfp = ZipFile(StringIO(zdata), "r")
    #data = zfp.read(zfp.namelist()[0])#.decode("cp1251")
    #del zfp
    #return data
    zfp = ZipFile(zdata)
    try :
        #python 2.6+
        return zfp.open(zfp.namelist()[0])
    except:
        return StringIO(zfp.read(zfp.namelist()[0]))#.decode("cp1251")

 
