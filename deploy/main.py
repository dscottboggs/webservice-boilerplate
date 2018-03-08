from deploy.config import Config
from docker.types import IPAMConfig, IPAMPool, Mount
import docker
import json
import os
import argparse
thisdir = os.path.dirname(os.path.realpath(__file__))
dc = Config.DOCKER_CLIENT
default_networks = ('bridge', 'host', 'none')
Mount = docker.types.Mount
project_root = os.path.join(thisdir, '..')
service_url = 'test.tams.tech'
admin_email = 'sysadmin@tams.tech'
images = {
    'nginx_proxy_container': "jwilder/nginx-proxy:latest",
    'letsencrypt_companion': "jrcs/letsencrypt-nginx-proxy-companion",
    'service': 'nginx:latest'
}

argument_parser = argparse.ArgumentParser(
    description="A boilerplate for a web service deployed behind an nginx reverse proxy with letsencrypt automated TLS."
)
argument_parser.add_argument(
    "stop", default=False, action='store_true'
)
argument_parser.add_argument(
    '--no-remove', default=False, action='store_true'
)
args = argument_parser.parse_args()
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

if not args.no_remove:
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
nginx_proxy_container = dc.containers.create(
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
        )
    ],
    network=testnetwork.name,
    ports={
        80:  80,
        443: 443
    },
    detach=True
)
letsencrypt_companion = dc.containers.create(
    name="letsencrypt-companion",
    image=images['letsencrypt_companion'],
    volumes_from=nginx_proxy_container.id,
    network=testnetwork.name,
    detach=True
)
web_service = dc.containers.create(
    name="test-webserver",
    image=images['service'],
    mounts=[
        Mount(
            type='bind',
            target='/usr/share/nginx/html',
            source=getdir(web_service_root, "service", "webroot"),
            read_only=True,
        ),
        Mount(
            type='bind',
            target='/etc/nginx',
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
    ports={
        80:  80,
    },
    detach=True,
)

containers = {
    container.name:container for container in (
        nginx_proxy_container, letsencrypt_companion, web_service
    )
}

if not args.stop:
    for container in containers.values():
        container.start()
