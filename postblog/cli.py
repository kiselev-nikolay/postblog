from pathlib import Path
from fire import Fire
from jinja2 import Environment, FileSystemLoader
from datetime import datetime as Datetime
from pprint import pprint
import shutil
from typing import Iterable
import yaml


class Time:
    def __init__(self, post_time: Datetime):
        self.dt = post_time.astimezone()
        self.pub = self.dt.strftime('%a, %d %b %Y %X %z')


class CommandLineInterface:
    def __init__(self):
        self.web_path = Path('site')
        self.config_path = Path('postblog.yml')
        self.assets_path = Path(__file__).parent / 'assets'
        self.c = {
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
        if self.config_path.exists():
            with open(self.config_path, 'r') as file:
                self.c.update(yaml.load(file, Loader=yaml.SafeLoader))
        self.data = {
            'articles': [],
            'page': {
                'name': 'Machine and me'
            }
        }
        self.env = Environment(
            loader=FileSystemLoader(
                str(self.assets_path.absolute())
            )
        )
    
    def init(self):
        if self.web_path.exists():
            shutil.rmtree(self.web_path)
        self.web_path.mkdir()
        with open(self.config_path, 'w') as file:
            yaml.dump(self.c, file)
        new_assets = self.web_path / 'assets'
        if not new_assets.exists():
            new_assets.mkdir()
        for asset in self.assets_path.iterdir():
            if asset.name[-3:] != '.j2':
                shutil.copyfile(asset, new_assets / asset.name)

    def _get_link(self, title: str, post_time: Time):
        return '{}/{}/{}/{}'.format(
            post_time.dt.year,
            post_time.dt.month,
            post_time.dt.day,
            title.lower().replace(' ', '_')
        )

    def post(self, title: str, text: str, categories: Iterable[str]):
        post_time = Time(Datetime.now())
        self.data['articles'].append({
            'title':       title,
            'text':        text,
            'link':        self._get_link(title, post_time),
            'publication': post_time.pub,
            'categories':  categories,
        })
        self.check()

    def check(self):
        pprint(self.config_path.absolute())
        pprint(self.assets_path.absolute())
        pprint(self.c)
    
    def build(self):
        with open(self.web_path / 'feed.xml', 'w') as file:
            t = self.env.get_template('rss.xml.j2')
            file.write(t.render(last_build=Time(Datetime.now()).pub,
                                **self.c, **self.data))


def main():
    Fire(CommandLineInterface())
