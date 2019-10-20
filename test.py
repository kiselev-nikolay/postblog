from subprocess import Popen, PIPE


def test_smoke():
    for command in ['clear', 'init', 'build', 'clear']:
        with Popen(['pipenv', 'run', 'postblog', command], stderr=PIPE) as p:
            if p.stderr.read():
                raise Exception('{} failed'.format(command))
