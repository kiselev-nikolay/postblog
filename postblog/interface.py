from typing import Iterable, Dict
from pathlib import Path
import warnings
import shutil
import pickle
from time import time_ns
from datetime import datetime as Datetime
from jinja2 import Environment, FileSystemLoader
import yaml
import webbrowser
import uvicorn

from ._web import create_app
from .style import color_gen
from . import VERSION


class Time:
    def __init__(self, post_time: Datetime):
        self.dt = post_time.astimezone()
        self.pub = self.dt.strftime('%a, %d %b %Y %X %z')


class Interface:
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

        if self._config_path.exists():
            with open(self._config_path, 'r') as file:
                self._config = yaml.load(file, Loader=yaml.SafeLoader)
        else:
            with open(self._assets_templates / '_postblog.yml', 'r') as file:
                self._config = yaml.load(file, Loader=yaml.SafeLoader)

        self._web = {
            'posts': [],
            'pages': {}
        }

        self._env = Environment(
            loader=FileSystemLoader(
                str(self._build_path.absolute())
            )
        )

        self._analytics = {}
        self._analytics_storage = self._storage / 'analytics.bin'
        if self._analytics_storage.exists():
            with open(self._analytics_storage, 'rb') as file:
                self._analytics.update(pickle.load(file))

    def _refresh_web_posts(self):
        posts = [p for p in self._posts.iterdir()]
        for post_path in reversed(sorted(posts)):
            with open(post_path) as file:
                yield yaml.load(file, Loader=yaml.SafeLoader)

    def _refresh_web_pages(self):
        pages = [p for p in self._pages.iterdir()]
        for page_path in reversed(sorted(pages)):
            with open(page_path) as file:
                yield yaml.load(file, Loader=yaml.SafeLoader)

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
    
    def clear(self):
        for directory in [self._web_path, self._storage, self._build_path]:
            if directory.exists():
                shutil.rmtree(directory)

    def init(self):
        if self._web_path.exists():
            shutil.rmtree(self._web_path)
        self._web_path.mkdir()
        
        with open(self._config_path, 'w') as file:
            yaml.dump(self._config, file)

        self._build_path.mkdir(exist_ok=True)

        for asset in self._assets_templates.iterdir():
            if asset.is_file() and asset.name[0] != '_':
                shutil.copyfile(asset, self._build_path / asset.name)

        self._index_path = self._assets_templates / '_index.yml'
        shutil.copyfile(self._index_path, self._storage / 'pages/index.yml')

        self.build()

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
    
    def edit_config(self, field: str, key: str, value: str):
        self._config[field][key] = value
        with open(self._config_path, 'w') as file:
            yaml.dump(self._config, file)
        self.build()

    def set_config(self, config: Dict[str, Dict[str, str]]):
        self._config = config
        with open(self._config_path, 'w') as file:
            yaml.dump(self._config, file)
        self.build()

    def get_config(self):
        return self._config

    def _write_analytics(self, key, value):
        self._analytics[key] = value
        with open(self._analytics_storage, 'wb') as file:
            pickle.dump(self._analytics, file)

    def get_analytics(self):
        return self._analytics
    
    def build(self):
        start = time_ns()

        self._web = {
            'posts': [],
            'pages': []
        }

        if self._web_path.exists():
            shutil.rmtree(self._web_path)
        self._web_path.mkdir()

        assets_path = self._web_path / 'assets'

        assets_path.mkdir()

        for asset in self._build_path.iterdir():
            if asset.is_file() and asset.name[-3:] != '.j2' and asset.name[0] != '_':
                shutil.copyfile(asset, assets_path / asset.name)

        with open(assets_path / 'style.css', 'w') as file:
            t = self._env.get_template('style.css.j2')
            file.write(t.render(**self._config['theme'], color=color_gen))

        for post in self._refresh_web_posts():
            self._web['posts'].append(post)
            post_path = self._web_path / 'news' / post['link']
            post_path.parent.mkdir(exist_ok=True, parents=True)
            with open(post_path, 'w') as file:
                t = self._env.get_template('post.html.j2')
                file.write(t.render(last_build=Time(Datetime.now()).pub,
                                    page=dict(name=post['title'], base='../../../../'),
                                    post=post,
                                    **self._config, **self._web))

        for page in self._refresh_web_pages():
            self._web['pages'].append(page)
            with open(self._web_path / (page['link'] + '.html'), 'w') as file:
                t = self._env.get_template('page.html.j2')
                file.write(t.render(last_build=Time(Datetime.now()).pub,
                                    page=dict(base='', **page),
                                    **self._config, **self._web))
        
        (self._web_path / 'news').mkdir(exist_ok=True)
        with open(self._web_path / 'news/index.html', 'w') as file:
            t = self._env.get_template('news.html.j2')
            file.write(t.render(last_build=Time(Datetime.now()).pub,
                                page=dict(name='News', base='../'),
                                **self._config, **self._web))

        with open(self._web_path / 'feed.xml', 'w') as file:
            t = self._env.get_template('rss.xml.j2')
            file.write(t.render(last_build=Time(Datetime.now()).pub,
                                generator='Postblog {}'.format(VERSION),
                                **self._config, **self._web))

        with open(self._web_path / 'manifest.json', 'w') as file:
            t = self._env.get_template('manifest.json.j2')
            file.write(t.render(last_build=Time(Datetime.now()).pub,
                                **self._config, **self._web))
        
        self._write_analytics('build_speed', time_ns() - start)

    def admin(self):
        message = '"postblog admin" is deprecated and will be removed ' \
                  'since version 1.0.0. Use "postblog open --help" instead'
        warnings.simplefilter('once')
        warnings.warn(message, DeprecationWarning)
        self.open(dashboard=True)

    def open(self, dashboard: bool = False, view: bool = False, server: bool = False, debug: bool = False):
        app = create_app(self, debug)

        self.build()

        host = '0.0.0.0' if server else '127.0.0.1'

        if dashboard:
            webbrowser.open_new_tab('http://{}:8060/dashboard/'.format(host))
        if view:
            webbrowser.open_new_tab('http://{}:8060/site/'.format(host))
    
        uvicorn.run(app, host=host, port=8060)
