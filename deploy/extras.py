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

