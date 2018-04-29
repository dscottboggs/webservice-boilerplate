"""Accept input of folders, create docker volumes, put the files in them.

The files have to go into the docker volumes via .tar files, which are stored
in /tmp.
"""
import click
import docker
import os
import tarfile
from os import sep as root
from docker.types import Mount
from typing import Dict, Tuple, Optional, Union
from strict_hint import strict
from logging import getLogger, DEBUG #, WARN, INFO
from logging.config import dictConfig
from misc_functions import list_recursively, check_isdir, hash_of_str
DEBUG_LEVEL = DEBUG
def get_logging_config():
    """Check for a loggercfg.json file, or return a default config."""
    try:
        with open("loggercfg.json") as cfg:
            return cfg
    except FileNotFoundError:
        return {
            "version": 1,
            "formatters": {
                "brief": {
                    'format':
                        "%(levelname)s [%(asctime)s] %(filename)s@%(lineno)s:"
                        + " %(message)s"
                },
                "friendly": {
                    'format':
                        "In %(filename)s, at line %(lineno)s, a message was"
                        + " logged. Message follows:\n\t%(message)s\nThis"
                        + " message was logged by the function %(funcName)s,"
                        + " with\n%(levelname)s(%(levelno)s) severity,"
                        + " at %(asctime)s."
                }
            },
            "handlers": {
                "testhandler": {
                    "class": "logging.StreamHandler",
                    "formatter": "brief",
                    "level": DEBUG_LEVEL
                }
            },
            "root": {
                "handlers": ["testhandler"],
                "level": DEBUG_LEVEL
            }
        }
dictConfig(get_logging_config())
logger = getLogger()

parent_directory_name = os.path.basename(
    os.path.dirname(os.path.realpath(__file__))
)
FOLDERS: Dict[str, str]
PREFIX: str

@click.command()
@click.option(
    '--prefix',
    default=parent_directory_name,
    help="The prefix to assign to each volume to avoid name collisions."
)
# @click.option(
#     '-o',
#     '--folder-of-folders',
#     help="A folder containing folders you wish to become individual volumes."
# )
@click.option('-f', '--folder', multiple=True)
@strict
def main(prefix: str, folder_of_folders: Optional[str], folder: str) -> None:
    """Accept folders and populate the content to docker volumes.

    A prefix to apply to each volume can be specified; otherwise the parent
    folder which you placed this script into will be used.

    Folders must be in the format /local/folder:/destination/mount.
    """
    global FOLDERS, PREFIX
    PREFIX = prefix
    # if folder_of_folders and folder:
    #     logger.critical(
    #         "You can't specify both folder-of-folders and individual folders!"
    #     )
    #     exit(1)
    # elif folder_of_folders:
    #     FOLDERS = [
    #         d for d in os.listdir(folder_of_folders) if os.path.isdir(d)
    #     ]
    # else:
    def split(d: str) -> Tuple[str, str]:
        if len(d.split(':')) != 2:
            raise ValueError(
                f"{d} must be in the format /local/folder:/destination/mount."
            )
        return d.split(':')

    FOLDERS = { split(d)[0]:split(d)[1] for d in folder.split('\n') }



@strict
def get_mount_for(
            self,
            source: Union[str, tarfile.TarFile],
            destination: str,
            mount_point: str
        ) -> Tuple[Mount, str]:
    """Return a mount and the location of a tarfile to put in that mount.

    source should be the location of the source files
    destination should be the mount point inside the container
    mount_point should be the host mount point.
    """
    tmpstore = os.path.join(
        root, 'tmp', 'quick_deployments', 'tmpstore'
    )
    check_isdir(tmpstore)
    if isinstance(source, str):
        with tarfile.open(os.path.join(
                    tmpstore, '%s.tar' % hash_of_str(mount_point)[:15]
                ), 'w') as tf:
            for f in list_recursively(source):
                tf.add(f)
    else:
        os.makedirs(tmpstore)
        # Extract the received tarfile into a temporary storage.
        source.extractall(tmpstore)
        # then write the temporary storage to a new archive.
        with tarfile.open(os.path.join(
                    root,
                    'tmp',
                    'quick_deployments',
                    '%s.tar' % hash_of_str(mount_point)[:15]
                ), 'w') as tf:
            for f in list_recursively(tmpstore):
                tf.add(f)
        for f in list_recursively(tmpstore):
            os.remove(f)
        os.removedirs(tmpstore)
    mnt = Mount(
        target=destination,
        source=mount_point,
        type='bind',
        read_only=True
    )
    return mnt, os.path.join(
        root,
        'tmp',
        'quick_deployments',
        '%s.tar' % hash_of_str(mount_point)[:15]
    )


if __name__ == '__main__':
    main()
