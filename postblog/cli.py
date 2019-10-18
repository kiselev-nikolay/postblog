from pathlib import Path
from fire import Fire
from jinja2 import Environment, FileSystemLoader
from datetime import datetime as Datetime
from pprint import pprint
import shutil
from typing import Iterable
import yaml
import webbrowser


class Time:
    def __init__(self, post_time: Datetime):
        self.dt = post_time.astimezone()
        self.pub = self.dt.strftime('%a, %d %b %Y %X %z')


class CommandLineInterface:
    def __init__(self):
        self._assets_templates = Path(__file__).parent / 'assets'

        self._storage = Path('storage')
        self._pages = self._storage / 'pages'
        self._posts = self._storage / 'posts'

        self._storage.mkdir(exist_ok=True)
        self._pages.mkdir(exist_ok=True)
        self._posts.mkdir(exist_ok=True)

        self._config_path = self._storage / 'postblog.yml'

        self._web_path = Path('site')
        self._build_path = Path('assets')

        self._config = {
            'site': {
                'name':        'Machine and me',
                'author':      'Kiselev Nikolay',
                'description': 'Site about something original or not',
                'script_js':   'console.log("Somebody watching me")',
                'link':        'https://test.machineand.me',
                'formcarry':   'https://formcarry.com/s/...',
                'theme': {
                    'color': '#00bebe'
                }
            },
            'contact': {
                'name':    'Nikolay',
                'twitter': '@machineand_me'
            },
            'assets': {
                'favicon':  'favicon.png',
                'cover':    'cover.png',
                'manifest': 'manifest.webmanifest'
            }
        }

        if self._config_path.exists():
            with open(self._config_path, 'r') as file:
                self._config.update(yaml.load(file, Loader=yaml.SafeLoader))

        self._web = {
            'posts': [],
            'pages': []
        }

        self._env = Environment(
            loader=FileSystemLoader(
                str(self._build_path.absolute())
            )
        )
    
    def clear(self):
        for directory in [self._web_path, self._storage, self._build_path]:
            shutil.rmtree(directory)

    def init(self):
        if self._web_path.exists():
            shutil.rmtree(self._web_path)
        self._web_path.mkdir()
        
        with open(self._config_path, 'w') as file:
            yaml.dump(self._config, file)

        self._build_path.mkdir(exist_ok=True)

        for asset in self._assets_templates.iterdir():
            if asset.is_file():
                shutil.copyfile(asset, self._build_path / asset.name)

        self.build()

    def _refresh_web_posts(self):
        for post_path in self._posts.iterdir():
            with open(post_path) as file:
                yield yaml.load(file, Loader=yaml.SafeLoader)

    def _refresh_web_pages(self):
        self._pages

    def _get_link(self, title: str, post_time: Time):
        exists = True
        while exists:
            link = '{}/{}/{}/{}.html'.format(
                post_time.dt.year,
                post_time.dt.month,
                post_time.dt.day,
                title.lower().replace(' ', '_')
            )
            exists = (self._web_path / link).exists()
            title += '_'
        return link

    def post(self, title: str, text: str, categories: Iterable[str]):
        post_time = Time(Datetime.now())
        post = {
            'title':       title,
            'text':        text,
            'link':        self._get_link(title, post_time),
            'publication': post_time.pub,
            'categories':  categories,
        }
        post_save_path = self._posts / (post['link'].replace('/', '_') + '.yml')
        with open(post_save_path, 'w') as file:
            yaml.dump(post, file)
        self.build()
    
    def build(self):
        if self._web_path.exists():
            shutil.rmtree(self._web_path)
        self._web_path.mkdir()

        assets_path = self._web_path / 'assets'

        assets_path.mkdir()

        for asset in self._build_path.iterdir():
            if asset.is_file() and asset.name[-3:] != '.j2':
                shutil.copyfile(asset, assets_path / asset.name)

        with open(self._web_path / 'feed.xml', 'w') as file:
            t = self._env.get_template('rss.xml.j2')
            file.write(t.render(last_build=Time(Datetime.now()).pub,
                                **self._config, **self._web))

        with open(self._web_path / 'index.html', 'w') as file:
            t = self._env.get_template('index.html.j2')
            file.write(t.render(last_build=Time(Datetime.now()).pub,
                                page=dict(name='Home', base=''),
                                **self._config, **self._web))
        
        for post in self._refresh_web_posts():
            self._web['posts'].append(post)
            post_path = self._web_path / post['link']
            post_path.parent.mkdir(exist_ok=True, parents=True)
            with open(post_path, 'w') as file:
                t = self._env.get_template('post.html.j2')
                file.write(t.render(last_build=Time(Datetime.now()).pub,
                                    page=dict(name=post['title'], base='../../../'),
                                    post=post,
                                    **self._config, **self._web))

    def admin(self):
        from starlette.applications import Starlette
        from starlette.routing import Router, Mount
        from starlette.staticfiles import StaticFiles
        from starlette.responses import JSONResponse, RedirectResponse
        from starlette.middleware.cors import CORSMiddleware

        import uvicorn

        app = Starlette()
        app.add_middleware(CORSMiddleware, allow_origins=['*'], max_age=0)

        app.mount('/site', app=StaticFiles(directory=self._web_path, html=True), name="static")
        app.mount('/dashboard', app=StaticFiles(directory=self._assets_templates / 'admin', html=True), name="static")

        @app.route('/')#, methods=['post'])
        async def _homepage(request):
            return RedirectResponse('/dashboard')

        @app.route('/butler', methods=['post'])
        async def _butler(request):
            query = await request.json()
            command = getattr(self, query['command'])
            if query.get('args') and hasattr(query.get('args'), 'keys'):
                responce = command(**query['args'])
            else:
                responce = command()
            return JSONResponse(responce or {'status': 'complete'})
            # try:
            #     if query.get('args') and hasattr(query.get('args'), 'keys'):
            #         responce = command(**query['args'])
            #     else:
            #         responce = command()
            #     return JSONResponse(responce or {'status': 'complete'})
            # except Exception:
            #     return JSONResponse({'status': 'failed'})

        self.build()

        webbrowser.open_new_tab('http://127.0.0.1:8060/dashboard')

        uvicorn.run(app, host='127.0.0.1', port=8060)


def main():
    Fire(CommandLineInterface())
