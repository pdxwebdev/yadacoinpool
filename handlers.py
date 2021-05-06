import os
import time
import requests
from tornado.web import Application, StaticFileHandler
from yadacoin.http.base import BaseHandler
from yadacoin.core.chain import CHAIN


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


class PoolInfoHandler(BaseWebHandler):
    async def get(self):
        def get_ticker():
            return requests.get('https://safe.trade/api/v2/peatio/public/markets/tickers')
        
        try:
            if not hasattr(self.config, 'ticker'):
                self.config.ticker = get_ticker()
                self.config.last_update = time.time()
            if (time.time() - self.config.last_update) > (600 * 6):
                self.config.ticker = get_ticker()
                self.config.last_update = time.time()
            last_btc = self.config.ticker.json()['ydabtc']['ticker']['last']
        except:
            last_btc = 0
            
        shares_count = await self.config.mongo.async_db.shares.count_documents({'index': { '$gte': self.config.LatestBlock.block.index - 10}})
        blocks_found = await self.config.mongo.async_db.share_payout.count_documents({})
        last_block_found_payout = await self.config.mongo.async_db.share_payout.find_one({}, sort=[('index', -1)])
        last_block_found = await self.config.mongo.async_db.blocks.find_one({'index': last_block_found_payout['index']})
        prev_block = await self.config.mongo.async_db.blocks.find_one({'index': self.config.LatestBlock.block.index - 10})
        seconds_elapsed = int(self.config.LatestBlock.block.time) - int(prev_block['time'])
        self.render_as_json({
            'pool': {
                'hashes_per_second': (shares_count * 1000) / float(seconds_elapsed / 60), # it takes 1000H/s to produce 1 0x0000f... share per minute
                'miner_count': len(self.config.poolServer.inbound_streams['Miner'].keys()),
                'last_block': last_block_found['time'] if last_block_found else 0,
                'payout_scheme': 'PPLNS',
                'pool_fee': self.config.pool_take,
                'blocks_found': blocks_found,
                'min_payout': 0,
                'url': f'{self.config.peer_host}:{self.config.stratum_pool_port}'
            },
            'network': {
                'height': self.config.LatestBlock.block.index,
                'reward': CHAIN.get_block_reward(self.config.LatestBlock.block.index),
                'last_block': self.config.LatestBlock.block.time
            },
            'market': {
                'last_btc': last_btc
            }
        })


HANDLERS = [
    (r'/pool-info', PoolInfoHandler),
    (r'/pool-stats', PoolStatsInterfaceHandler),
    (r'/yadacoinpoolstatic/(.*)', StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), 'static')}),
]
