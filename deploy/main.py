from deploy.config import Config
from docker.types import Mount
import docker
from sys import argv
from extras import *

dc = Config.DOCKER_CLIENT
Mount = docker.types.Mount

args = parseargs(argv)

if not args['no_remove'] and not args['stop']:
    wipeclean()

testnetwork = dc.networks.create(
    name="TestNetwork",
    driver="bridge",
    ipam=get_subnet()
)

check_images(Config.images)

if not dc.swarm.init(advertise_addr=Config.ADVERTISE_ADDR):
    print(msg("Swarm init failed!"))
    exit(2)

# ^^ filepath of a working directory
nginx_proxy_container = dc.services.create(
# see help(dc.containers.run), create()'s documentation refers to it
    name="nginx-proxy-container",
    image=Config.images['nginx_proxy_container'],
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
            source=getdir(Config.volumes_folder, "nginx-proxy", "conf")
        ),
        Mount(
            type='bind',
            target="/usr/share/nginx/html",
            source=getdir(Config.volumes_folder, "nginx-proxy", "webroot")
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
    image=Config.images['letsencrypt_companion'],
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
        "{}.MYSQL_PASSWORD".format(Config.service_name): get_new_password(),
        "{}.MYSQL_USER".format(Config.service_name): Config.service_name,
    }:
    Config.SECRETS.create_secret(
        name, secret
    )

wordpress_database = dc.containers.create(
    name='_'.join(Config.service_name, "database"),
    image=Config.images['wordpress_database'],
    network=testnetwork.name,
    environment={
        "MYSQL_USER_FILE": secretpath('.'.join(Config.service_name, "MYSQL_USER")),
        "MYSQL_RANDOM_ROOT_PASSWORD": True,
        "MYSQL_PASSWORD_FILE": secretpath(
            '.'.join(Config.service_name, "MYSQL_PASSWORD")
        ),
    },
    secrets=[
        Config.secrets.get_secret('.'.join(Config.service_name, "MYSQL_PASSWORD")),
        Config.secrets.get_secret('.'.join(Config.service_name, "MYSQL_USER")),
    ],
    mounts=[
        Mount(
            type='bind',
            target='/var/lib/mysql',
            source=getdir(Config.volumes_folder, "service", "database"),
            read_only=True
        )
    ],
    detach=True
)
wordpress_blog = dc.containers.create(
    name=Config.service_name,
    image=Config.images['wordpress_blog'],
    mounts=[
        Mount(
            type='bind',
            target='/var/www/html',
            source=getdir(Config.volumes_folder, "service", "webroot"),
            read_only=True,
        ),
        Mount(
            type='bind',
            target='/etc/apache2',
            source=getdir(Config.volumes_folder, "service", "conf"),
            read_only=True,
        )
    ],
    environment={
        'VIRTUAL_HOST': Config.service_url,
        'DEFAULT_HOST': Config.service_url,
        'LETSENCRYPT_HOST': Config.service_url,
        'LETSENCRYPT_EMAIL': Config.admin_email,
        'WORDPRESS_DB_HOST': '_'.join(Config.service_name, "database"),
        'WORDPRESS_DB_USER_FILE': secretpath(
            '.'.join(Config.service_name, "MYSQL_USER")
        ),
        'WORDPRESS_DB_PASSWORD_FILE': secretpath(
            '.'.join(Config.service_name, "MYSQL_PASSWORD")
        )
    },
    secrets=[
        Config.secrets.get_secret("{}.MYSQL_PASSWORD".format(Config.service_name)),
        Config.secrets.get_secret("{}.MYSQL_USER".format(Config.service_name))
    ],
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
print(msg(
    "Successfully created",
    json.dumps(tuple(containers.keys()), indent=2),
    "containers",
    sep='\n'
))
if not args['stop']:
    for container in containers.values():
        print(msg("starting container", container.name))
        container.start()
