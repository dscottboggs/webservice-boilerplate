user { 'www-data':
  ensure => present,
  home   => '/var/www',
  shell  => '/usr/sbin/nologin',
  uid    => '33',
  gid    => '33',
}
