from starlette.applications import Starlette
from starlette.routing import Router, Mount
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware


def create_app(interface, debug = False):
    app = Starlette()
    app.add_middleware(CORSMiddleware, allow_origins=['*'], max_age=0)

    app.mount('/site', app=StaticFiles(directory=interface._web_path, html=True), name="static")
    app.mount('/dashboard', app=StaticFiles(directory=interface._assets_templates / 'admin', html=True), name="static")

    @app.route('/')
    async def _homepage(request):
        return RedirectResponse('/dashboard')

    @app.route('/news/')
    async def _homepage(request):
        return RedirectResponse('/site/news')

    @app.route('/butler', methods=['post'])
    async def _butler(request):
        query = await request.json()
        command = getattr(interface, query['command'])
        if debug:
            if query.get('args') and hasattr(query.get('args'), 'keys'):
                responce = command(**query['args'])
            else:
                responce = command()
            return JSONResponse(responce or {'status': 'complete'})
        else:
            try:
                if query.get('args') and hasattr(query.get('args'), 'keys'):
                    responce = command(**query['args'])
                else:
                    responce = command()
                return JSONResponse(responce or {'status': 'complete'})
            except Exception:
                return JSONResponse({'status': 'failed'})

    return app