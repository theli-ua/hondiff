from fetcher import ARCHS
from google.appengine.ext import db


class Version(db.Model):
    value = db.StringProperty(required=True)
    imported = db.BooleanProperty(default=False)
    arch = db.IntegerProperty(default=ARCHS.LINUX_RETAIL)


def version_ok(arch,version):
    if len(version.split('.')) != 4:
        version += '.0'
    return Version.get_or_insert(version,value=version,arch=arch)

def version_arch(version):
    v = Version.get_by_key_name(version)
    if v: return v.arch
    return None
    

def get_versions(arch=None):
    if arch is None:
        return [d.value for d in Version.all()]
    else:
        return [d.value for d in db.GqlQuery('Select * from Version where arch = {0}'.format(arch)).fetch(1000)]
