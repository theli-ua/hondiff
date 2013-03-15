


diffext = ['.interface','.interfaceset','.mdf','.entity','.material','.effect', \
        '.package', '.str', '.txt', '.upgrades', '.gamemechanics', '.lua', \
        '.resources', '.cfg', '/worldconfig', '.vsh', '.psh','.xml']

xmlext =  ['.interface','.interfaceset','.mdf','.entity','.material','.effect', \
        '.package', '.upgrades', '.gamemechanics', \
        '.resources', '/worldconfig','.xml']

luaext = ['.lua']

def is_diffable(path):
    for ext in diffext:
        if path.endswith(ext):
            return True
    return False

def get_lang(path):
    if not is_diffable(path):
        return 'None'
    for ext in xmlext:
        if path.endswith(ext):
            return 'xml'
    for ext in luaext:
        if path.endswith(ext):
            return 'lua'
    return 'text'

