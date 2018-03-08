# encoding: utf-8
# copyright: 2018, D. Scott Boggs, Jr.

require 'strings'

home_dir = "/home/scott"
service_names = ['test-webserver']
service_urls = ['test']
services = {
  'test_webserver' => {
    'url' => 'test',
    'page' => test_webserver_page_200,
    'redirectpage' => test_webserver_page_301
  }
}
domain = 'tams.tech'
docker_folder = "#{home_dir}/Documents/boilerplate/webservice/files/DockerVolumes"
#base_dir = "#{docker_folder}/#{service_name}"
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
  describe http('http://localhost/') do
    its('status') { should cmp 503 }
    its('body') { should cmp page_503 }
  end
  services.each do |svc_name, service|
    describe docker_container(svc_name) do
      it { should exist }
      it { should be_running }
    end
    describe http("http://#{url}.#{domain}/") do
      its('status') { should cmp 301 }
      its('body') { should cmp service['redirectpage'] }
    end
    describe http("https://#{url}.#{domain}/") do
      its('status') { should cmp 200 }
      its('body') { should cmp service['page'] }
      its('headers.Content-Type') { should cmp 'text/html' }
    end
  end
end
