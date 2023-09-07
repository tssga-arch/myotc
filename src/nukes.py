#!/usr/bin/env python3
'''
Handling Nuking of resources
'''
import myotc
import consts as K
import openstack

###################################################################
#
# Nuking
#
###################################################################

def cname_match(prefix, rs):
  ''' Compare several resource record CNAME's in one go

  :param str prefix: prefix to check
  :param list rs: list of resources to test
  '''

  for r in rs:
    if r.startswith(prefix):
      return True
  return False

def nuke(c, sid, doIt = False, def_priv_zone='localnet', def_public_zone= None):
  ''' Main function to destroy OTC resources

  :param openstack.connection c: Connection to OpenStack environment
  :param str sid: system ID for the environment being destroyed
  :param bool doIt: (optional) Defaults to False, if true, will only show what would happen, but nothing will be destroyed.
  :param str def_priv_zone: (optional) Default private zone used by this environment
  :param str def_public_zone: (optional) Public DNS zone where records have been stored.
  '''
  dryRun = not doIt
  prefix = sid + '-'

  # Remove automatic DNS entries
  zone_name = '{}.{}'.format(sid,def_priv_zone)
  zn = c.dns.find_zone(myotc.sanitize_dns_name(zone_name),zone_type=K.private)
  if zn:
    if dryRun:
      print('WONT remove DNS internal zone {}'.format(zone_name))
    else:
      myotc.msg('Removing DNS internal zone {}...'.format(zone_name))
      c.dns.delete_zone(zn)
      myotc.msg('DONE\n')

  if not def_public_zone is None:
    zone_name = def_public_zone
    zn = c.dns.find_zone(myotc.sanitize_dns_name(zone_name))
    if not zn is None:
      for rs in c.dns.recordsets(zn):
        if K.NAME in rs:
          if rs[K.NAME].startswith(sid):
            if dryRun:
              print('WONT remove DNS record for {}'.format(rs[K.NAME]))
              continue
            else:
              myotc.msg('Removing DNS record for {}...'.format(rs[K.NAME]))
              c.dns.delete_recordset(rs,zn)
              myotc.msg('DONE\n')
              continue
        if K.type in rs:
          if rs[K.type] == K.CNAME:
            if cname_match(prefix, rs[K.records]):
              if dryRun:
                print('WONT remove DNS record for {}'.format(rs[K.NAME]))
              else:
                myotc.msg('Removing DNS record for {}...'.format(rs[K.NAME]))
                c.dns.delete_recordset(rs,zn)
                myotc.msg('DONE\n')

  else:
    print('Not modifying Public DNS records (Missing PUBLIC_DNS_ZONE definition)')


  # Go first through servers to identify all port-ids
  port_ids = {}
  for s in c.compute.servers():
    if K.NAME in s:
      if s[K.NAME].startswith(sid):
        i = 0
        for interface in c.compute.server_interfaces(s):
          port_ids[interface[K.port_id]] = '{server}-if{port}'.format(server = s[K.NAME], port = i)
          ++i

  for ip in c.network.ips():
    if ip.port_id in port_ids:
      if dryRun:
        print('WONT release IP {ip} from server port {port}'.format(ip=ip.floating_ip_address, port = port_ids[ip.port_id]))
      else:
        myotc.msg('Releasing IP {ip} from server port {port}...'.format(ip=ip.floating_ip_address, port = port_ids[ip.port_id]))
        c.network.delete_ip(ip)
        myotc.msg('DONE\n')

  # delete all servers
  for s in c.compute.servers():
    if K.NAME in s:
      if s[K.NAME].startswith(prefix):
        if dryRun:
          print('WONT delete vm {}'.format(s[K.NAME]))
        else:
          myotc.msg('Deleting vm {}...'.format(s[K.NAME]))
          c.compute.delete_server(s[K.sID])
          c.compute.wait_for_delete(s)
          myotc.msg('DONE\n')

  # delete all left-over volumes...
  for v in c.block_store.volumes():
    if K.NAME in v:
      if v[K.NAME].startswith(prefix):
        if dryRun:
          print('WONT delete volume {}'.format(v[K.NAME]))
        else:
          myotc.msg('Deleting volume {}...'.format(v[K.NAME]))
          c.block_store.delete_volume(v)
          myotc.msg('DONE\n')

  # Find all the relevant routers
  routers = []
  for r in c.network.routers():
    if K.NAME in r:
      if r[K.NAME].startswith(prefix):
        routers.append(r)

  # Delete all targeted subnets
  for sn in c.network.subnets():
    if K.NAME in sn:
      if sn[K.NAME].startswith(prefix):
        if dryRun:
          print('WONT delete subnet {}'.format(sn[K.NAME]))
        else:
          for r in routers:
            myotc.msg('Disconnecting vpc {vpc} from subnet {sn}...'.format(vpc = r.name, sn = sn.name))
            try:
              c.network.remove_interface_from_router(r.id, sn.id)
            except openstack.exceptions.ResourceNotFound:
              myotc.msg('(NOT CONNECTED)\n')
            else:
              myotc.msg('DONE\n')

          myotc.msg('Deleting subnet {}...'.format(sn[K.NAME]))
          c.network.delete_subnet(sn[K.sID])
          myotc.msg('DONE\n')

  # Delete all targeted networks
  for n in c.network.networks():
    if K.NAME in n:
      if n[K.NAME].startswith(prefix):
        if dryRun:
          print('WONT delete net {}'.format(n[K.NAME]))
        else:
          myotc.msg('Deleting net {}...'.format(n[K.NAME]))
          c.network.delete_network(n[K.sID])
          myotc.msg('DONE\n')

  # Delete internal dnz zone
  zname = '{}.'.format(sid,def_priv_zone)
  idnsz = c.dns.find_zone(myotc.sanitize_dns_name(zname),zone_type=K.private)
  if idnsz:
    if dryRun:
      print('WONT delete internal DNS zone {}'.format(zname))
    else:
      myotc.msg('Deleting internal DNS zone {}...'.format(zname))
      c.dns.delete_zone(idnsz)
      myotc.msg('DONE\n')

  # Delete network security groups
  for g in c.network.security_groups():
    if K.NAME in g:
      if g[K.NAME].startswith(prefix):
        if dryRun:
          print('WONT delete sg {}'.format(g[K.NAME]))
        else:
          myotc.msg('Deleting sg {}...'.format(g[K.NAME]))
          c.network.delete_security_group(g[K.sID])
          myotc.msg('DONE\n')


  # Delete VPCs (aka routers)
  for r in c.network.routers():
    if K.NAME in r:
      if r[K.NAME].startswith(prefix):
        if dryRun:
          print('WONT delete vpc {}'.format(r[K.NAME]))
        else:
          myotc.msg('Deleting vpc {}...'.format(r[K.NAME]))
          c.network.delete_router(r[K.sID])
          myotc.msg('DONE\n')


  return
