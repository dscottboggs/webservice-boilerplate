# webservice-boilerplate
A boilerplate project for a web service deployed on docker behind an Nginx reverse proxy

Prerequisites:
  - A bourne-compatible shell
  - python3.5+ (perhaps 2.7 as well, I use 3.6 when writing.)
  - Docker -- the latest stable version (probably not the one from your
    distro's default repo)
  - inspec (https://www.inspec.io/downloads/)
  - Puppet if you want to use it to place your files and prepare anything
    necessary on your system. I decided it was mostly redundant in this case
    but I could still see someone using it or chef with this.
  - An internet connection with ports 80 and 443 forwarded to the parent
    machine and firewall allowed on those ports. If you can't access the
    internet in that way, you can't use this. The LetsEncrypt service needs
    to be able to make a request from the public to your machine to verify
    it.
  - A valid domain name or subdomain which you control and are able to point
    at the machine you will be using this on. Same reason as the above point.

All commands are written assuming your current working directory is the
root of the repository and all paths are relative to that location as well.

To deploy a service in this framework, replace the default "web_service"
service with the service you would like to deploy, design tests for InSpec and
put them in the /test/controls folder. Some baseline tests are already there.

Any files which need to be present and mounted to the docker container should
be placed in the /files/DockerVolumes/ folder, and then added to the container's
mounts, as shown in the example service.

Once you are sure all your files are in place and as you want them to be, run
/test/libraries/generate_file_test.py, and place the output in a .rb file in
/test/controls. This means that every time you run `inspec exec test`, you'll
be notified if a file has changed.

Once all the tests and files are in place on your host, be sure you have your
domains pointed and your ports opened, then run `python3 setup.py install` to
install the dependencies for the python scripts (docker) and run the script at
/deploy/main.py. This will REMOVE AND STOP **ALL** currently existing
containers. If you don't want it to do that, you can try passing '--no-remove',
but this option is untested and probably won't work.

Once you've run /deploy/main.py, your service should be up and running on your
system. Run `inspec exec test` to run the tests, and enjoy your web applications!
