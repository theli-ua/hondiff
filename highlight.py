from webapp_cached import CachedRequestHandler

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from filetypes import get_lang,is_diffable
import fetcher
from templates import get_template


def pygmentize(lang, code):
    lexer = get_lexer_by_name(lang)
    formatter = HtmlFormatter()
    return highlight(code, lexer, formatter)


class  HoNFileViewer(CachedRequestHandler):
    def get_page(self,arch,version,path):
        lang = self.request.query_string
        if lang == "":
            lang = 'text'
        if not is_diffable(path):
            return 'Sorry, viewing this types of files is not allowed'
        data = fetcher.fetch(arch,version,path)
        if data is None:
            self.response.out.write( 'Sorry, could not fetch file %s for version %s.<br>' % \
                    (version,path))
            return None
        else:
            data = data.read()
            try:
                data = data.decode('utf8')
            except:
                data = data.decode('cp1251')
                
            template_values = { 'data' : pygmentize(lang,data) }

            template = get_template('highlight.html')
            return template.render(template_values)
       

