from deploy.config import Config
from docker.types import IPAMConfig, IPAMPool, Mount
import docker
import json
import os
from sys import argv
from stat import S_IRUSR as OWNER_READ
from stat import S_IWUSR as OWNER_WRITE
from subprocess import run, PIPE
thisdir = os.path.dirname(os.path.realpath(__file__))
dc = Config.DOCKER_CLIENT
default_networks = ('bridge', 'host', 'none', 'docker_gwbridge', "ingress")
Mount = docker.types.Mount
project_root = '/'.join(thisdir.split('/')[:-1]) # parent dir of the current dir
print("Project root is: ", project_root)
service_url = 'test.tams.tech'
admin_email = 'sysadmin@tams.tech'
images = {
    'traefik': "traefik:1.3.6-alpine",
    'service': 'nginx'
}

sh_exec = lambda cmd: run(
    cmd, shell=True, check=True, stdin=PIPE, stdout=PIPE, stderr=PIPE
)

args = {
    'stop': "stop" in argv,
    'no_remove': "--no-remove" in argv
}
if len(argv) > 1 and not args.values():
    print(
        "A boilerplate for a web service deployed behind an nginx reverse proxy",
        "with letsencrypt automated TLS.",
        "   Options:",
        "       stop            stops the services instead of starting them",
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

traefik_folder = os.path.join(project_root, "files", "traefik", "etc")
traefik_files = {
    'encryptionStore': os.path.join(traefik_folder,"letsencrypt_store.json"),
    'traefikLog': os.path.join(traefik_folder, "traefik.log"),
    'accessLog': os.path.join(traefik_folder, "traefik_access.log")
}
for filename in traefik_files.values():
    if not os.access(filename, os.F_OK):
        open(filename, 'w').close()
if not os.access(traefik_files['encryptionStore'], os.F_OK):
    os.chmod(traefik_files['encryptionStore'], mode=OWNER_READ|OWNER_WRITE)
    sh_exec('sudo chown root:root {}'.format(traefik_files['encryptionStore']))

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
traefik_container = dc.containers.create(
    name="traefik-proxy",
    image=images["traefik"],
    network=testnetwork.id,
    command=Config.traefik_command,
    mounts=[
        Mount(
            type='bind',
            target="/var/run/docker.sock",
            source=Config.DOCKER_SOCKET_FILE_LOCATION,
            read_only=True
        ),
        Mount(
            type='bind',
            target='/etc',
            source=os.path.join(
                project_root, "files", "traefik", "etc"
            )
        ),
    ],
    ports={
        80: 80,
        443:443
    },
    labels={
        'traefik.frontend.rule': "Host:monitor.tams.tech",
        'traefik.port': '8080'
    }
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
    labels={
        "traefik.backend":          "test",
        "traefik.frontend.rule":    "Host:test.tams.tech",
        "traefik.docker.network":   "proxy",
        "traefik.port":             "80"
    },
    network=testnetwork.name,
    detach=True,
)

containers = {
    container.name:container for container in (
        traefik_container, web_service
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
