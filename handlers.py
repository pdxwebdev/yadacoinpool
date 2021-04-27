import os
from yadacoin.http.base import BaseHandler


class BaseWebHandler(BaseHandler):

    def prepare(self):

        if self.request.protocol == 'http' and self.config.ssl:
            self.redirect('https://' + self.request.host + self.request.uri, permanent=False)

    def get_template_path(self):
        return os.path.join(os.path.dirname(__file__), 'templates')

class PoolStatsInterfaceHandler(BaseWebHandler):
    async def get(self):
        self.render(
            'pool-stats.html',
            yadacoin=self.yadacoin_vars,
            username_signature=self.get_secure_cookie("username_signature"),
            username=self.get_secure_cookie("username"),
            rid=self.get_secure_cookie("rid"),
            title='YadaCoin - Pool Stats',
            mixpanel='pool stats page'
        )


HANDLERS = [
    (r'/pool-stats', PoolStatsInterfaceHandler),
]
