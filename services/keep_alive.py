import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def _health(request):
    return web.Response(text="OK")


async def run_keep_alive_server(port: int):
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Keep-alive server {port} portda ishga tushdi")
