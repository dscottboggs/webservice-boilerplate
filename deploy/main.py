from deploy.config import Config
from docker.types import IPAMConfig, IPAMPool, Mount
import docker
import json
import os
__file__ = "main.py"
thisdir = os.path.dirname(os.path.realpath(__file__))
dc = Config.DOCKER_CLIENT
default_networks = ('bridge', 'host', 'none')
Mount = docker.types.Mount
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

wipeclean()

testnetwork = dc.networks.create(
    name="TestNetwork",
    driver="bridge",
    ipam=get_subnet()
)

test_webserver_root = getdir(
    os.sep,
    'home',
    'scott',
    'Documents',
    'basic_nginx_deployment',
    "files",
    "test-webserver"
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

basic_web_server.start()
