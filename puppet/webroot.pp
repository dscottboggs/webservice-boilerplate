# puppet file for config dir
$home_dir = '/home/scott'
$service_name = 'test-webserver'
$puppet_folder = "${home_dir}/Documents/basic_nginx_deployment/puppet"
$docker_folder = "${home_dir}/Documents/basic_nginx_deployment/files"
$base_dir = "${docker_folder}/${service_name}"
$container_name = "files_${service_name}_1"
$webroot = "${base_dir}/webroot"
$src_dir = "${puppet_folder}/web"
$nginx_default_index = '<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working. Further configuration is required.</p>

<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a>.<br/>
Commercial support is available at
<a href="http://nginx.com/">nginx.com</a>.</p>

<p><em>Thank you for using nginx.</em></p>
</body>
</html>
'
$nginx_50x_page = '<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>
'

file { $docker_folder:
  ensure => directory,
}
file { $base_dir:
  ensure => directory,
}
file { $src_dir:
  ensure => directory,
}
file { "${src_dir}/index.html":
  ensure  => file,
  content => 'sha256:38ffd4972ae513a0c79a8be4573403edcd709f0f572105362b08ff50cf6de521'
}
file { $webroot:
  ensure => directory,
}
file { "${webroot}/index.html":
  ensure  => file,
  mode    => '0644',
  group   => '0',
  owner   => '0',
  content => $nginx_default_index
}
file { "${webroot}/50x.html":
  ensure => file,
  mode => '0644',
  group   => '0',
  owner   => '0',
  content => $nginx_50x_page
}
