#!/usr/bin/env python3
#
# Handling Nuking of resources
#
# ~ import openstack

###################################################################
#
# Nuking
#
###################################################################

def cname_match(prefix, rs):
  for r in rs:
    if r.startswith(prefix):
      return True
  return False

def nuke(c, sid, doIt = False, def_priv_zone='localnet', def_public_zone='public.zone'):
  dryRun = not doIt
  prefix = sid + '-'

  # Remove automatic DNS entries
  zone_name = '{}.{}'.format(sid,def_priv_zone)
  zn = c.dns.find_zone(zone_name,zone_type='private')
  if zn:
    if dryRun:
      print('WONT remove DNS internal zone {}'.format(zone_name))
    else:
      c.dns.delete_zone(zn)
      print('Removed DNS internal zone {}'.format(zone_name))

  zone_name = def_public_zone
  zn = c.dns.find_zone(zone_name)
  if not zn is None:
    for rs in c.dns.recordsets(zn):
      if 'name' in rs:
        if rs['name'].startswith(sid):
          if dryRun:
            print('WONT remove DNS record for {}'.format(rs['name']))
            continue
          else:
            c.dns.delete_recordset(rs,zn)
            print('Removed DNS record for {}'.format(rs['name']))
            continue
      if 'type' in rs:
        if rs['type'] == 'CNAME':
          if cname_match(prefix, rs['records']):
            if dryRun:
              print('WONT remove DNS record for {}'.format(rs['name']))
            else:
              c.dns.delete_recordset(rs,zn)
              print('Removed DNS record for {}'.format(rs['name']))

  # Go first through servers to identify all port-ids
  port_ids = {}
  for s in c.compute.servers():
    if 'name' in s:
      if s['name'].startswith(sid):
        i = 0
        for interface in c.compute.server_interfaces(s):
          port_ids[interface['port_id']] = '{server}-if{port}'.format(server = s['name'], port = i)
          ++i

  for ip in c.network.ips():
    if ip.port_id in port_ids:
      if dryRun:
        print('WONT release IP {ip} from server port {port}'.format(ip=ip.floating_ip_address, port = port_ids[ip.port_id]))
      else:
        c.network.delete_ip(ip)
        print('Released IP {ip} from server port {port}'.format(ip=ip.floating_ip_address, port = port_ids[ip.port_id]))

  # delete all servers
  for s in c.compute.servers():
    if 'name' in s:
      if s['name'].startswith(prefix):
        if dryRun:
          print('WONT delete vm {}'.format(s['name']))
        else:
          c.compute.delete_server(s['id'])
          c.compute.wait_for_delete(s)
          print('Deleted vm {}'.format(s['name']))

  # delete all left-over volumes...
  for v in c.block_store.volumes():
    if 'name' in v:
      if v['name'].startswith(prefix):
        if dryRun:
          print('WONT delete volume {}'.format(v['name']))
        else:
          c.block_store.delete_volume(v)
          print('Delete volume {}'.format(v['name']))

  # Find all the relevant routers
  routers = []
  for r in c.network.routers():
    if 'name' in r:
      if r['name'].startswith(prefix):
        routers.append(r)

  # Delete all targeted subnets
  for sn in c.network.subnets():
    if 'name' in sn:
      if sn['name'].startswith(prefix):
        if dryRun:
          print('WONT delete subnet {}'.format(sn['name']))
        else:
          for r in routers:
            # ~ try:
              c.network.remove_interface_from_router(r.id, sn.id)
              print('Disconnected vpc {vpc} from subnet {sn}'.format(vpc = r.name, sn = sn.name))

          c.network.delete_subnet(sn['id'])
          print('Deleted subnet {}'.format(sn['name']))

  # Delete all targeted networks
  for n in c.network.networks():
    if 'name' in n:
      if n['name'].startswith(prefix):
        if dryRun:
          print('WONT delete net {}'.format(n['name']))
        else:
          c.network.delete_network(n['id'])
          print('Deleted net {}'.format(n['name']))

  # Delete internal dnz zone
  zname = '{}.'.format(sid,def_priv_zone)
  idnsz = c.dns.find_zone(zname,zone_type='private')
  if idnsz:
    if dryRun:
      print('WONT delete internal DNS zone {}'.format(zname))
    else:
      c.dns.delete_zone(idnsz)
      print('Deleted internal DNS zone {}'.format(zname))

  # Delete VPCs (aka routers)
  for r in c.network.routers():
    if 'name' in r:
      if r['name'].startswith(prefix):
        if dryRun:
          print('WONT delete vpc {}'.format(r['name']))
        else:
          c.network.delete_router(r['id'])
          print('Deleted vpc {}'.format(r['name']))

  # Delete network security groups
  for g in c.network.security_groups():
    if 'name' in g:
      if g['name'].startswith(prefix):
        if dryRun:
          print('WONT delete sg {}'.format(g['name']))
        else:
          c.network.delete_security_group(g['id'])
          print('Deleted sg {}'.format(g['name']))

  print('DONE')
