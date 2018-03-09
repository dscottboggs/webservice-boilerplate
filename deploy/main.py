from deploy.config import Config
from docker.types import IPAMConfig, IPAMPool, Mount
import docker
import json
import os
from sys import argv
thisdir = os.path.dirname(os.path.realpath(__file__))
dc = Config.DOCKER_CLIENT
default_networks = ('bridge', 'host', 'none')
Mount = docker.types.Mount
project_root = os.path.join(thisdir, '..')
service_url = 'test.tams.tech'
admin_email = 'sysadmin@tams.tech'
images = {
    'nginx_proxy_container': "jwilder/nginx-proxy",
    'letsencrypt_companion': "jrcs/letsencrypt-nginx-proxy-companion",
    'wordpress_blog': 'wordpress',
    'wordpress_database': 'mariadb'
}

args = {
    'stop': "stop" in argv or "--stop" in argv,
    'no_remove': "--no-remove" in argv
}
if len(argv) > 1 and not args.values():
    print(
        "A boilerplate for a web service deployed behind an nginx reverse proxy",
        "with letsencrypt automated TLS.",
        "   Options:",
        "       stop, --stop    Doesn't start the containers up at the end.",
        "       --no-remove     doesn't remove old containers. Will likely",
        "                       lead to errors.")

def getdir(*args):
    """Create dir if not exists

    Full path should be passed as individual arguments, as they are forwarded
    to os.path.join()"""
    if not os.path.isdir(os.path.join(*args)):
        os.makedirs(os.path.join(*args))
    return os.path.join(*args)
volumes_folder = getdir(thisdir, "volumes")
def wipeclean():
    """Remove all current networks and containers."""
    containers = lambda running=False: dc.containers.list(all=not running)
    networks = dc.networks.list
    for container in containers(running=True):
        container.stop()
    for container in containers():
        container.remove()
    if len(containers()):
        print("Current list of containers is not empty:", containers())
        for container in containers(running=True):
            print(container, "is running still.")
        exit(1)
    for network in networks():
        if network.name not in default_networks:
            network.remove()
def get_subnet():
    return IPAMConfig(pool_configs=[IPAMPool(subnet=Config.available_subnets.pop())])
def pull(repository, tag=None):
    for status in dc.api.pull(repository, tag=tag or 'latest', stream=True):
        status = json.loads(status.decode())
        if 'progress' in status.keys():
            print(status['status'], status['progress'])

if not args['no_remove'] and not args['stop']:
    wipeclean()

testnetwork = dc.networks.create(
    name="TestNetwork",
    driver="bridge",
    ipam=get_subnet()
)

for img in images.values():
    # check for images and pull if necessary.
    if img not in dc.images.list(all=True):
        if ":" in img:
            pull(
                repository=img.split(':', maxsplit=1)[0],
                tag=img.split(':', maxsplit=1)[1]
            )
        else:
            pull(repository=img)

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
wordpress_database = dc.services.create(
    name="wordpress_database",
    image=images['wordpress_database'],
    network=testnetwork.name,
    detach=True
)
wordpress_blog = dc.services.create(
    name="test-webserver",
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
        'LETSENCRYPT_EMAIL': admin_email
    },
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
print(
    "Successfully created",
    json.dumps(tuple(containers.keys()), indent=2),
    "containers",
    sep='\n'
)
if not args['stop']:
    for container in containers.values():
        print("starting container", container.name)
        container.start()
