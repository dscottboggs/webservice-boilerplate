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

if not args.no_remove:
    wipeclean()

testnetwork = dc.networks.create(
    name="TestNetwork",
    driver="bridge",
    ipam=get_subnet()
)

web_service_root = getdir(project_root, "files", "web-service")
# ^^ filepath of a working directory
nginx_proxy_container = dc.containers.create(
# see help(dc.containers.run), create()'s documentation refers to it
    name="nginx-proxy-container",
    image="jwilder/nginx-proxy:latest",
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
            source=getdir(project_root, "files", "nginx-proxy-config")
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
    image="jrcs/letsencrypt-nginx-proxy-companion",
    volumes_from=nginx_proxy_container,
    network=testnetwork.name,
    detach=True
)
basic_web_server = dc.containers.create(
    name="test-webserver",
    image='nginx:latest',
    mounts=[
        Mount(
            type='bind',
            target='/usr/share/nginx/html',
            source=getdir(test_webserver_root, "webroot"),
            read_only=True,
        ),
        Mount(
            type='bind',
            target='/etc/nginx',
            source=getdir(test_webserver_root, "config"),
            read_only=True,
        )
    ],
    environment={'testvalue': "asdfjkl;"},
    network=testnetwork.name,
    ports={
        80:  80,
        443: 443
    },
    detach=True,
)

containers = {
    container.name:container for container in (
        nginx_proxy_container, letsencrypt_companion, basic_web_server
    )
}

if not args.stop:
    for container in containers.values():
        container.start()
