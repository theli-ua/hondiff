from webapp_cached import CachedRequestHandler
import templates


class  CAI(CachedRequestHandler):
    redirect_latest = False
    def get_page(self,arch,accountid):
        try:
            count = int(self.request.query_string)
        except:
            count = 50

        accountid = int(accountid)
        if count == 0:
            count = 50
        base_url = 'http://s3.amazonaws.com/naeu-icb/icons/%d/%d/%d/' % \
                ( accountid / 1000000, (accountid % 1000000 ) / 1000, accountid )

        base_url += '%d.cai'

        template_values = {
                'base_url' : base_url,
                'count' : count,
                }
        template = templates.get_template('cai.html')
        return template.render(template_values)
