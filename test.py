from subprocess import Popen, PIPE


def test_smoke():
    for command in ['clear', 'init', 'build', 'clear']:
        with Popen(['pipenv', 'run', 'postblog', command], stderr=PIPE) as p:
            error = p.stderr.read()
            if error:
                raise Exception('{} failed with {}'.format(command, error))
