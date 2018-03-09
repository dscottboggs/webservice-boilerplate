def msg(msg, *args):
    """Handle an assertion message without needing to write dedent/wrap every
    time.

    Also passes args to str.format."""
    outstr = ""
    msg = dedent(msg)
    for line in wrap(msg.format(*args)):
        outstr+=line+'\n'
    return outstr

def parseargs(argv):
    if len(argv) > 1 and not args.values():
        print(
            "A boilerplate for a web service deployed behind an nginx reverse proxy",
            "with letsencrypt automated TLS.",
            "   Options:",
            "       stop, --stop    Doesn't start the containers up at the end.",
            "       --no-remove     doesn't remove old containers. Will likely",
            "                       lead to errors.")
        exit()
    return {
        'stop': "stop" in argv or "--stop" in argv,
        'no_remove': "--no-remove" in argv
    }

def getdir(*args):
    """Create dir if not exists

    Full path should be passed as individual arguments, as they are forwarded
    to os.path.join()"""
    if not os.path.isdir(os.path.join(*args)):
        os.makedirs(os.path.join(*args))
    return os.path.join(*args)

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

secretpath = lambda sn: os.path.join(os.sep, "var", "run", "secrets", sn)

def check_images(images):
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

def _baseN(num,b,numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    """Convert a number to any base up to 36"""
    return ((num == 0) and numerals[0]) or (baseN(
        num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

def _num_to_alpha(num, randval=False):
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

get_new_password = lambda entropy=250: _num_to_alpha(entropy, randval=True)
