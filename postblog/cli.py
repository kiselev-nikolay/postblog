from pathlib import Path
from fire import Fire
from jinja2 import Environment, FileSystemLoader
from datetime import datetime as Datetime
from pprint import pprint
from typing import Iterable


class Time:
    def __init__(self, post_time: Datetime):
        self.dt = post_time.astimezone()
        self.pub = self.dt.strftime('%a, %d %b %Y %X %z')


class CommandLineInterface:
    def __init__(self):
        self.config_path = Path('postblog.yml')
        self.assets_path = Path(__file__).parent / 'assets'
        self.data = {
            'site': {
                'name':       'Machine & me',
                'author':     'Kiselev Nikolay',
                'decription': 'Lorem ipsum dor sit',
                'last_build': Time(Datetime.now()).pub,
                'analytics':  '',
                'links': {
                    'home': 'https://test.machineand.me',
                    'rss':  'https://test.machineand.me/feed.xml'
                },
                'theme': {
                    'color': '#00bebe'
                }
            },
            'contact': {
                'name':    'Nikolay',
                'twitter': '@machineand_me'
            },
            'assets': {
                'favicon':  'image.png',
                'cover':    'cover.png',
                'manifest': 'manifest.webmanifest'
            },
            'articles': [],
            'page': {
                'name': 'Machine & me'
            }
        }
        self.env = Environment(
            loader=FileSystemLoader(
                str(self.assets_path.absolute())
            )
        )

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
        pprint(self.data)
    
    def render(self):
        t = self.env.get_template('base.html.j2')
        print(t.render(**self.data))


def main():
    Fire(CommandLineInterface())
