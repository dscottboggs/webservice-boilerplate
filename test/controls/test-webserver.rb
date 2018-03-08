# encoding: utf-8
# copyright: 2018, D. Scott Boggs, Jr.

title 'Configuration tests'

home_dir = "/home/scott"
service_names = ['test-webserver']
service_urls = ['test']
domain = 'tams.tech'
docker_folder = "#{home_dir}/Documents/boilerplate/webservice/files/DockerVolumes"
base_dir = "#{docker_folder}/#{service_name}"
proxy_dir = "#{docker_folder}/nginx-proxy"

control 'manual_tests' do
  impact 0.7
  title 'Container checks'
  desc 'Manual checks to make sure the containers are in place and behaving.'
  describe docker_container("letsencrypt-companion") do
    it { should exist }
    it { should be_running }
  end
  describe docker_container("nginx-proxy-container") do
    it { should exist }
    it { should be_running }
    its('ports') { should cmp "0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp"}
  end
  for service in service_names do
    describe docker_container(service) do
      it { should exist }
      it { should be_running }
    end
  end
  describe http('http://localhost/') do
    its('status') { should cmp 503 }
  end
  for url in service_urls do
    describe http("http://#{url}.#{domain}/") do
      its('status') { should cmp 301 }
    end
    describe http("https://#{url}.#{domain}/") do
      its('status') { should cmp 200 }
      its('body') { should cmp nginx_default_index }
      its('headers.Content-Type') { should cmp 'text/html' }
    end
  end
end
