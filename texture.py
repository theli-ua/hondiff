from webapp_cached import CachedRequestHandler
from dds import dds2png
import fetcher

class  HoNTexture(CachedRequestHandler):
    content_type = 'image/png'
    def get_page(self,arch,version,path):
        dds = fetcher.fetch(arch,version,path)
        return dds2png(dds)

