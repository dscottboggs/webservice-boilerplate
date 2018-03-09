import docker
import logging
import random
from logging.config import dictConfig
from os import makedirs as mkdir
from os.path import dirname as parent_dir_of
from os.path import realpath as find
from os.path import join as makepath
from os.path import isdir
from textwrap import dedent, wrap

def get_docker_client(location, api_version):
    from docker import DockerClient
    return DockerClient(location, api_version)

def getdir(*args):
    """Create dir if not exists

    Full path should be passed as individual arguments, as they are forwarded
    to os.path.join()"""
    if not isdir(makepath(*args)):
        mkdir(makepath(*args))
    return makepath(*args)

def get_logging_config():
    try:
        with open("loggercfg.json") as cfg:
            return cfg
    except FileNotFoundError:
        return None

loggingConfig = get_logging_config() or {
    "version": 1,
    "formatters": {
        "brief": {
            'format':
                "%(levelname)s [%(asctime)s] %(filename)s@%(lineno)s: %(message)s"
        },
        "friendly":{
            'format': dedent("""
                In %(filename)s, at line %(lineno)s, a message was logged. Message follows:
                    %(message)s
                This message was logged by the function %(funcName)s, with
                %(levelname)s(%(levelno)s) severity, at %(asctime)s.""")
        }
    },
    "handlers": {
        "testhandler": {
            "class": "logging.StreamHandler",
            "formatter": "brief",
            "level": logging.DEBUG
        }
    },
    "root": {
        "handlers": ["testhandler"],
        "level": logging.DEBUG
    }
}

class SecretStore():
    """A place to store and retrieve docker secrets."""
    get_secret = lambda key: self.secrets[key]
    def __init__(self, daemon):
        self.secrets = {}
        self._get_secrets = daemon.secrets.list
        self._create_secret = daemon.secrets.create
    def create_secret(self, key: str, value: str):
        """Store a key-value pair as a docker secret."""
        for secret in self._get_secrets():
            if secret.name == key:
                secret.remove()
        self.secrets.update({
            key: self._create_secret(name=key, data=value)
        })
    def create_secrets(self, secrets: dict):
        """Do create_secret on a dict of secrets"""
        for name, secret in secrets.values():
            create_secret(name, secret)

class Config():
    """Configuration items"""
    DOCKER_SOCKET_FILE_LOCATION = "/run/docker.sock"
    DOCKER_SOCKET_LOCATION = "unix://{}".format(DOCKER_SOCKET_FILE_LOCATION)
    DOCKER_API_VERSION = '1.30'
    RELATIVE_ROOT = parent_dir_of(__name__)
    DOCKER_CLIENT = get_docker_client(DOCKER_SOCKET_LOCATION, DOCKER_API_VERSION)
    SECRETS = SecretStore(DOCKER_CLIENT)
    available_subnets = ["172.{}.0.0/16".format(x) for x in range(30,255)]
    dictConfig(loggingConfig)
    logger = logging.getLogger()
    IMAGE_PULL_TIMEOUT = 300
    ADVERTISE_ADDR = "192.168.1.1:21257"
    thisdir = parent_dir_of(find(__file__))
    volumes_folder = getdir(thisdir, '..', "files", "DockerVolumes")
    service_url = 'test.tams.tech'
    service_name = 'test_wordpress'
    admin_email = 'sysadmin@tams.tech'
    images = {
        'nginx_proxy_container': "jwilder/nginx-proxy",
        'letsencrypt_companion': "jrcs/letsencrypt-nginx-proxy-companion",
        'wordpress_blog': 'wordpress',
        'wordpress_database': 'mariadb'
    }
