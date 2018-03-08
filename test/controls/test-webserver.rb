# encoding: utf-8
# copyright: 2018, D. Scott Boggs, Jr.

title 'Configuration tests'

home_dir = "/home/scott"
service_name = container_name = 'test-webserver'
docker_folder = "#{home_dir}/Documents/boilerplate/webservice/files/DockerVolumes"
base_dir = "#{docker_folder}/#{service_name}"
proxy_dir = "#{docker_folder}/nginx-proxy"

control 'proxy' do
  impact 1
  title 'Check the reverse proxy container stuff'
  describe file("#{proxy_dir}/conf") do
    it { should be_directory }
  end
end

control 'service-volumes' do                        # A unique ID for this control
  impact 0.7                                # The criticality, if this control fails.
  title 'Check the volumes'                 # A human-readable title
  desc 'Check that the proper files are in place'
  # config files checks
  describe file("#{base_dir}/config") do
    it { should be_directory }
  end
  describe file("#{base_dir}/config/nginx.conf") do
    it { should be_file }
    its('sha256sum') { should cmp '772e914d404163a563e888730a3d4c5d86fbb1a5d3ee6b8c58c7eeda9af1db5b' }
  end
  describe file("#{base_dir}/config/conf.d/default.conf") do
    it { should be_file }
    its('sha256sum') { should cmp 'ba015afe3042196e5d0bd117a9e18ac826f52e44cb29321a9b08f7dbf48c62a5' }
  end
  # webroot checks
  describe file("#{base_dir}/webroot") do
    it { should be_directory }
  end
  describe file ("#{base_dir}/webroot/index.html") do
    it { should be_file }
    its('sha256sum') { should cmp '38ffd4972ae513a0c79a8be4573403edcd709f0f572105362b08ff50cf6de521'}
  end
end
control 'ports' do
  impact 0.7
  title 'Check the ports'
  desc 'Check that the ports are open on the container'
  describe docker_container(container_name) do
    it { should exist }
    it { should be_running }
    its('ports') { should cmp "0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp"}
  end
  describe http('http://localhost/') do
    its('status') { should cmp 301 }
  end
  describe http('https://localhost/') do
    its('status') { should cmp 200 }
    its('body') { should cmp nginx_default_index }
    its('headers.Content-Type') { should cmp 'text/html' }
  end
end
