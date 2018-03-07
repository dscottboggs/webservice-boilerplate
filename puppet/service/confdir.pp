# puppet file for config dir
$home_dir = '/home/scott'
$service_name = 'test-webserver'
$base_dir = "${home_dir}/Documents/boilerplates/webservice"
$puppet_folder = "${base_dir}/puppet"
$docker_folder = "${base_dir}/files"
$volumes_dir = "${docker_folder}/${service_name}"
$container_name = "files_${service_name}_1"
$confdir = "${volumes_dir}/config"
$src_dir = "${puppet_folder}/service/conf"

user { 'www-data':
  ensure => present,
  home   => '/var/www',
  shell  => '/usr/sbin/nologin',
  uid    => '33',
  gid    => '33',
}
file { $docker_folder:
  ensure => directory,
}
file { $base_dir:
  ensure => directory,
}
file { $src_dir:
  ensure => directory,
}
file { $confdir:
  ensure => directory,
  owner  => '0',
  group  => '0',
  mode   => '0755',
}
file { "${confdir}/conf.d":
  ensure => directory,
  mode   => '0755',
  owner  => '0',
  group  => '0'
}
file { "${confdir}/conf.d/default.conf":
  ensure => file,
  mode   => '0644',
  group  => '0',
  owner  => '0',
  source => "${src_dir}/conf.d/default.conf"
}
file { "${confdir}/fastcgi_params":
  ensure => file,
  mode   => '0644',
  group  => '0',
  owner  => '0',
  source => "${src_dir}/fastcgi_params"
}
file { "${confdir}/koi-utf":
  ensure => file,
  mode   => '0644',
  group  => '0',
  owner  => '0',
  source => "${src_dir}/koi-utf"
}
file { "${confdir}/koi-win":
  ensure => file,
  mode   => '0644',
  group  => '0',
  owner  => '0',
  source => "${src_dir}/koi-win"
}
file { "${confdir}/mime.types":
  ensure => file,
  mode   => '0644',
  group  => '0',
  owner  => '0',
  source => "${src_dir}/mime.types"
}
file { "${confdir}/nginx.conf":
  ensure => file,
  mode   => '0644',
  group  => '0',
  owner  => '0',
  source => "${src_dir}/nginx.conf"
}
file { "${confdir}/scgi_params":
  ensure => file,
  mode   => '0644',
  group  => '0',
  owner  => '0',
  source => "${src_dir}/scgi_params"
}
file { "${confdir}/uwsgi_params":
  ensure => file,
  mode   => '0644',
  group  => '0',
  owner  => '0',
  source => "${src_dir}/uwsgi_params"
}
file { "${confdir}/win-utf":
  ensure => file,
  mode   => '0644',
  group  => '0',
  owner  => '0',
  source => "${src_dir}/win-utf"
}
