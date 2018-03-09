import docker
import logging
import random
from extras import SecretStore
from logging.config import dictConfig
from os.path import dirname as parent_dir_of
from textwrap import dedent, wrap

def get_docker_client(location, api_version):
    from docker import DockerClient
    return DockerClient(location, api_version)


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
