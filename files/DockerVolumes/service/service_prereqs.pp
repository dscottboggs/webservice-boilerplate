# puppet file for this service
# add any additional system requirements here, then apply it before deploying.

user { 'www-data':
  ensure => present,
  home   => '/var/www',
  shell  => '/usr/sbin/nologin',
  uid    => '33',
  gid    => '33',
}
