from fabric.contrib.files import append, exists, sed
from fabric.api import env, local, run
import random

REPO_URL = 'https://github.com/Obii-wan/First-test.git'

env.warn_only = True


def deploy():
    site_folder = '/home/{user}/sites/{host}'.format(user=env.user, host=env.host)
    source_folder = site_folder + '/source'
    _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_settings(source_folder, env.host)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)


def _create_directory_structure_if_necessary(site_folder):
    for sub_folder in ('database', 'virtualenv', 'static', 'source'):
        run('mkdir -p {site_folder}/{sub_folder}'.format(site_folder=site_folder, sub_folder=sub_folder))


def _get_latest_source(source_folder):
    if exists(source_folder + '/.git'):
        run('cd {source_folder} && git fetch'.format(source_folder=source_folder))
    else:
        run('git clone {git_repo} {source_folder}'.format(git_repo=REPO_URL, source_folder=source_folder))
    current_commit = local('cd {source_folder} && git log -n 1 --format=%H'.format(source_folder=source_folder), capture=False)
    run('cd {source_folder} && git reset --hard {current_commit}'.format(source_folder=source_folder, current_commit=current_commit))
    run('mv {source_folder}/superlists/ {source_folder}/'.format(source_folder=source_folder))


def _update_settings(source_folder, site_name):
    settings_path = source_folder + '/superlists/settings.py'
    sed(settings_path, 'DEBUG = True', 'DEBUG = False')
    sed(settings_path, 'ALLOWED_HOSTS =.+$', 'ALLOWED_HOSTS = ["{site_name}"]'.format(site_name=site_name))
    secret_key_file = source_folder + '/superlists/secret_key.py'

    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, "SECRET_KEY = '{secret_key}'".format(secret_key=key))

    append(settings_path, '\nfrom .secret_key import SECRET_KEY')


def _update_virtualenv(source_folder):
    virtualenv_folder = source_folder + '/../virtualenv'

    if not exists(virtualenv_folder + '/bin/pip3'):
        run('virtualenv --python=python3 {virtualenv_folder}'.format(virtualenv_folder=virtualenv_folder))

    run('{virtualenv_folder}/bin/pip3 install -r {source_folder}/superlists/requirements.txt'.format(virtualenv_folder=virtualenv_folder, source_folder=source_folder))


def _update_static_files(source_folder):
    run('cd {source_folder} && ../virtualenv/bin/python3 manage.py collectstatic --noinput'.format(source_folder=source_folder))


def _update_database(source_folder):
    run("cd {source_folder} && ../virtualenv/bin/python3 manage.py migrate --noinput".format(source_folder=source_folder))
