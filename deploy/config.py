import docker
import logging
import random
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

def baseN(num,b,numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    """Convert a number to any base up to 36"""
    return ((num == 0) and numerals[0]) or (baseN(
        num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

def num_to_alpha(num, randval=False):
    """Convert a numeral value to alphanumeric

    That is, it converts the numeral value to a base36 (10 for 0-9 and 26 for
    a-z) number, which is really only useful to create random alphanumeric
    values for passwords based on a random number.

    If 'random' is True, num isn't the literal number to be converted, it's how
    many bits of entropy to gather for a random value."""
    if randval:
        return baseN(random.getrandbits(num), 36)
    else:
        return baseN(num, 36)

def msg(msg, *args):
    """Handle an assertion message without needing to write dedent/wrap every
    time.

    Also passes args to str.format."""
    outstr = ""
    msg = dedent(msg)
    for line in wrap(msg.format(*args)):
        outstr+=line+'\n'
    return outstr

class Config():
    """Configuration items"""

    DOCKER_SOCKET_FILE_LOCATION = "/run/docker.sock"
    DOCKER_SOCKET_LOCATION = "unix://{}".format(DOCKER_SOCKET_FILE_LOCATION)
    DOCKER_API_VERSION = '1.30'
    RELATIVE_ROOT = parent_dir_of(__name__)
    DOCKER_CLIENT = get_docker_client(DOCKER_SOCKET_LOCATION, DOCKER_API_VERSION)
    available_subnets = ["172.{}.0.0/16".format(x) for x in range(30,255)]
    dictConfig(loggingConfig)
    logger = logging.getLogger()
    IMAGE_PULL_TIMEOUT = 300
    traefik_command = "--configfile=/etc/traefik.toml"
