from deploy.config import Config
from docker.types import IPAMConfig, IPAMPool, Mount
import docker
import json
import os
from sys import argv
from extras import *
thisdir = os.path.dirname(os.path.realpath(__file__))
dc = Config.DOCKER_CLIENT
default_networks = ('bridge', 'host', 'none')
Mount = docker.types.Mount
project_root = os.path.join(thisdir, '..')
service_url = 'test.tams.tech'
service_name = 'test_wordpress'
admin_email = 'sysadmin@tams.tech'
images = {
    'nginx_proxy_container': "jwilder/nginx-proxy",
    'letsencrypt_companion': "jrcs/letsencrypt-nginx-proxy-companion",
    'wordpress_blog': 'wordpress',
    'wordpress_database': 'mariadb'
}

args = parseargs(argv)
volumes_folder = getdir(thisdir, "volumes")

if not args['no_remove'] and not args['stop']:
    wipeclean()

testnetwork = dc.networks.create(
    name="TestNetwork",
    driver="bridge",
    ipam=get_subnet()
)

check_images(images)

web_service_root = getdir(project_root, "files", "DockerVolumes")
# ^^ filepath of a working directory
nginx_proxy_container = dc.services.create(
# see help(dc.containers.run), create()'s documentation refers to it
    name="nginx-proxy-container",
    image=images['nginx_proxy_container'],
    mounts=[
        Mount(
            type='bind',
            target="/tmp/docker.sock",
            source=Config.DOCKER_SOCKET_FILE_LOCATION,
            read_only=True
        ),
        Mount(
            type='bind',
            target="/etc/nginx",
            source=getdir(web_service_root, "nginx-proxy", "conf")
        ),
        Mount(
            type='bind',
            target="/usr/share/nginx/html",
            source=getdir(web_service_root, "nginx-proxy", "webroot")
        )
    ],
    network=testnetwork.name,
    ports={
        80:  80,
        443: 443
    },
    detach=True
)
letsencrypt_companion = dc.services.create(
    name="letsencrypt-companion",
    image=images['letsencrypt_companion'],
    volumes_from=nginx_proxy_container.id,
    network=testnetwork.name,
    mounts=[
        Mount(
            type='bind',
            target="/var/run/docker.sock",
            source=Config.DOCKER_SOCKET_FILE_LOCATION,
            read_only=True
        )
    ],
    detach=True
)
for name, secret in {
        "{}.MYSQL_PASSWORD".format(service_name): get_new_password(),
        "{}.MYSQL_USER".format(service_name): service_name,
    }:
    Config.SECRETS.create_secret(
        name, secret
    )

wordpress_database = dc.containers.create(
    name='_'.join(service_name, "database"),
    image=images['wordpress_database'],
    network=testnetwork.name,
    environment={
        "MYSQL_USER_FILE": secretpath('.'.join(service_name, "MYSQL_USER")),
        "MYSQL_RANDOM_ROOT_PASSWORD": True,
        "MYSQL_PASSWORD_FILE": secretpath(
            '.'.join(service_name, "MYSQL_PASSWORD")
        ),
    },
    secrets=[
        Config.secrets.get_secret('.'.join(service_name, "MYSQL_PASSWORD")),
        Config.secrets.get_secret('.'.join(service_name, "MYSQL_USER")),
    ]
    mounts=[
        Mount(
            type='bind',
            target='/var/lib/mysql',
            source=getdir(web_service_root, "service", "database"),
            read_only=True
        )
    ]
    detach=True
)
wordpress_blog = dc.containers.create(
    name=service_name,
    image=images['wordpress_blog'],
    mounts=[
        Mount(
            type='bind',
            target='/var/www/html',
            source=getdir(web_service_root, "service", "webroot"),
            read_only=True,
        ),
        Mount(
            type='bind',
            target='/etc/apache2',
            source=getdir(web_service_root, "service", "conf"),
            read_only=True,
        )
    ],
    environment={
        'VIRTUAL_HOST': service_url,
        'DEFAULT_HOST': service_url,
        'LETSENCRYPT_HOST': service_url,
        'LETSENCRYPT_EMAIL': admin_email,
        'WORDPRESS_DB_HOST': '_'.join(service_name, "database"),
        'WORDPRESS_DB_USER_FILE': secretpath(
            '.'.join(service_name, "MYSQL_USER")
        ),
        'WORDPRESS_DB_PASSWORD_FILE': secretpath(
            '.'.join(service_name, "MYSQL_PASSWORD")
        )
    },
    secrets=[
        Config.secrets.get_secret("{}.MYSQL_PASSWORD".format(service_name))
        Config.secrets.get_secret("{}.MYSQL_USER".format(service_name))
    ]
    network=testnetwork.name,
    detach=True,
)

containers = {  # this is a "dictionary comprehension"
    container.name:container for container in (
        nginx_proxy_container,
        letsencrypt_companion,
        wordpress_blog,
        wordpress_database
    )
}
msg(
    "Successfully created",
    json.dumps(tuple(containers.keys()), indent=2),
    "containers",
    sep='\n'
)
if not args['stop']:
    for container in containers.values():
        msg("starting container", container.name)
        container.start()
