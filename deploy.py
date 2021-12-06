#!/usr/bin/env python3
import yaml
import base64

# ~ import openstack
# ~ import sys
# ~ import os
# ~ import fnmatch
# ~ import time
# ~ from datetime import datetime

# ~ import ypp
# ~ import nukes

from cfn import *

###################################################################
#
# Create new resources
#
###################################################################
SG_KEYS = ('remote_ip_prefix', 'protocol', 'port_range_min', 'port_range_max' )
SG_COPYKEYS = ('remote_ip_prefix', 'protocol', 'port_range_min', 'port_range_max', 'ethertype', 'remote_ip_prefix' )

def find_volume(c, vname):
  for v in c.block_store.volumes():
    if 'name' in v:
      if v['name'] == vname: return v
    if 'id' in v:
      if v['id'] == vname: return v
  return None

def new_vol(vol_name, dryrun=True, **kw):
  c = cf[CLOUD]
  sid = cf[SID]

  cvol = find_volume(c, vol_name)
  if cvol is None:
    # Make sure size is there...
    if not 'size' in kw:
      print('Unable to create volume {}. "size" not specified'.format(vol_name))
      return None
    cvol = c.block_store.create_volume(name=vol_name, **kw)
    c.block_store.wait_for_status(cvol,
                                  status='available',
                                  failures=['error'],
                                  interval=5,
                                  wait=120)
    print('Created volume {}'.format(cvol['name']))
  else:
    if cvol['size'] != kw['size']:
      # Volume has been resized...
      if dryrun:
        print('WONT resize volume {}'.format(volname))
      else:
        print('TODO: VOLUME RESIZING IS NOT IMPLEMENTED!')
  return cvol

def flatten_rules(rule_lst):
  ol = []
  for i in rule_lst:
    ol.append(yaml.dump(i))
  ol.sort()
  return yaml.dump(ol)

def new_sg(sg_name, rule_list, dryrun=True):
  c = cf[CLOUD]
  sid = cf[SID]

  # Convert rules
  # NOTE: We only support ingress rules!
  rules = []
  for sgrule in rule_list:
    rule = {
      'direction': 'ingress',
      'ethertype': 'IPv4',
      'remote_ip_prefix': None
    }
    if isinstance(sgrule,str):
      port_pair = sgrule.split('/',1)
      rule['protocol'] = port_pair[1]
      if ':' in port_pair[0]:
        port_pair = port_pair[0].split(':',1)
      else:
        port_pair[1] = port_pair[0]

      if int(port_pair[0]) < int(port_pair[1]):
        rule['port_range_min'] = int(port_pair[0])
        rule['port_range_max'] = int(port_pair[1])
      else:
        rule['port_range_min'] = int(port_pair[1])
        rule['port_range_max'] = int(port_pair[0])
    else:
      if 'ethertype' in sgrule:
        rule['ethertype'] = sgrule['ethertype']
      else:
        rule['ethertype'] = 'IPv4'
      for k in SG_KEYS:
        if k in sgrule:
          rule[k] = sgrule[k]
        else:
          rule[k] = None
    rules.append(rule)

  sg = c.network.find_security_group(sg_name)
  if sg:
    # Pre-process existing ruleset so we can compare it later
    oldrules = []
    for osr in sg['security_group_rules']:
      if osr['direction'] != 'ingress': continue # we only know how to deal with ingress rules
      ccr = {
        'direction': 'ingress',
      }
      for k in SG_COPYKEYS:
        if k in osr:
          ccr[k] = osr[k]
        else:
          ccr[k] = None
      oldrules.append(ccr)

    # stringify rulesets so we can easilty compare them
    if flatten_rules(oldrules) == flatten_rules(rules):
      # No changes needed!
      return sg
    else:
      # ~ print('OLD RULES====')
      # ~ print(flatten_rules(oldrules))
      # ~ print('NEW RULES====')
      # ~ print(flatten_rules(rules))

      if dryrun:
        print('WONT update rules in security group {sg}'.format(sg=sg_name))
        return sg


      # Get rid of the old rule set
      cnt = 0
      for osr in sg['security_group_rules']:
        if osr['direction'] != 'ingress': continue # we only know how to deal with ingress rules
        c.network.delete_security_group_rule(osr)
        cnt += 1
      if cnt:
        print('SG {sgname} flushed old rules: {count}'.format(sgname=sg_name,count=cnt))
  else:
    sg = c.network.create_security_group(name = sg_name)
    print('Created SG {}'.format(sg_name))

  cnt = 0
  for rule in rules:
    rule['security_group_id'] = sg.id
    # ~ print(rule)
    c.network.create_security_group_rule(**rule)
    cnt += 1
  print('SG {sgname} rules added: {count}'.format(sgname=sg_name, count=cnt))

  return sg

def new_vpc(dryrun=True,**attrs):
  c = cf[CLOUD]
  sid = cf[SID]

  vpcname = '{}-vpc1'.format(sid)
  vpc = c.network.find_router(vpcname)
  if not vpc:
    vpc = c.network.create_router(name=vpcname)
    print('Created vpc {}'.format(vpcname))

    if 'snat' in attrs:
      snat = attrs['snat']
    else:
      snat = True

    vpc = c.network.update_router(vpc.id,
        external_gateway_info = {
          'enable_snat': snat,
          'network_id': vpc['external_gateway_info']['network_id']
        }
    )
  else:
    if 'snat' in attrs:
      snat = bool(attrs['snat'])
      if bool(vpc['external_gateway_info']['enable_snat']) != snat:
        if dryrun:
          print('vpc {} needs to change snat setting to {}'.format(vpcname,snat))
        else:
          vpc = c.network.update_router(vpc.id,
              external_gateway_info = {
                'enable_snat': snat,
                'network_id': vpc['external_gateway_info']['network_id']
              }
          )
          print('vpc {} changed snat setting to {}'.format(vpcname,snat))

  # Always create an internal dnz zone
  zname = '{}.{}'.format(sid,cf[DEFAULT_PRIVATE_DNS_ZONE])
  idnsz = c.dns.find_zone(zname,zone_type='private')
  if not idnsz:
    idnsz = c.dns.create_zone(
        name=zname,
        router = { 'router_id': vpc.id },
        zone_type='private'
    )
    print('Created internal DNS zone {}'.format(zname))

  return vpc

def flatten_rs(lst):
  r = list(lst)
  r.sort()
  return yaml.dump(r)

def find_rrs(zn,rtype,name):
  c = cf[CLOUD]

  for rs in c.dns.recordsets(zn):
    if ('name' in rs) and ('type' in rs):
      if rs['name'] == name and rs['type'] == rtype:
        return rs
  return None

def del_dns(zname, zone_type, bsname, rtype, dryrun=True):
  c = cf[CLOUD]

  dnszn = c.dns.find_zone(zname,zone_type=zone_type)
  if not dnszn: return None
  name = '{}.{}'.format(bsname,zname)

  cset = find_rrs(dnszn, rtype, name)
  if cset:
    if dryrun:
      print('WONT update DNS {type} record for {name}'.format(type=rtype,name=name))
    else:
      c.dns.delete_recordset(cset,dnszn)
      print('Deleted DNS {type} record for {name}'.format(type=rtype,name=name))

def new_dns(zname, zone_type, bsname, rtype, rrs, dryrun=True):
  # ~ print([zname,zone_type, bsname, rtype, rrs, dryrun])
  c = cf[CLOUD]

  dnszn = c.dns.find_zone(zname,zone_type=zone_type)
  if not dnszn: return None
  name = '{}.{}'.format(bsname,zname)

  cset = find_rrs(dnszn, rtype, name)
  if cset:
    if len(rrs):
      if flatten_rs(cset['records']) != flatten_rs(rrs):
        # So record changed
        if dryrun:
          print('WONT update DNS {type} record for {name}'.format(type=rtype,name=name))
        else:
          c.dns.delete_recordset(cset,dnszn)
          c.dns.create_recordset(dnszn, name=name, type = rtype, records = rrs)
          print('Updated DNS {type} record for {name}'.format(type=rtype,name=name))
    else:
      if dryrun:
        print('WONT delete DNS {type} record for {name}'.format(type=rtype,name=name))
      else:
        c.dns.delete_recordset(cset,dnszn)
        print('Deleted DNS {type} record for {name}'.format(type=rtype,name=name))
  else:
    if len(rrs):
      c.dns.create_recordset(dnszn, name=name, type = rtype, records = rrs)
      print('Created DNS {type} record for {name}'.format(type=rtype,name=name))

def new_net(id_or_name, dryrun=True, cidr_tmpl=None, **attrs):
  c = cf[CLOUD]
  sid = cf[SID]
  prefix = sid + '-'

  name = gen_name(id_or_name,'sn')

  netname = '{}net'.format(name)
  net = c.network.find_network(netname)
  if not net:
    net = c.network.create_network(name = netname)
    print('Created network {}'.format(netname))


  if 'vpc' in attrs:
    vpcname = attrs['vpc']
  else:
    vpcname = '{}-vpc1'.format(sid)
  vpc = c.network.find_router(vpcname)
  if not vpc:
    print('Error: unable to create net {net}.  Missing vpc {vpc}'.format(net=name, vpc=vpcname))
    return None

  snx = c.network.find_subnet(name)
  if not snx:
    if not 'cidr' in attrs:
      if isinstance(id_or_name,int):
        if cidr_tmpl is None:
          cidr = cf[DEFAULT_NET_FORMAT].format(id=id_or_name, id_hi=int(id_or_name/256), id_lo=int(id_or_name % 256))
        else:
          cidr = cidr_tmpl.format(id=id_or_name, id_hi=int(id_or_name/256), id_lo=int(id_or_name % 256))
      else:
        print('new_net(snid={snid}): must specify CIDR'.format(snid = id_or_name))
        return None
    else:
      cidr = attrs['cidr']

    args = {
      'name': name,
      'is_dhcp_enabled': True,
      'dns_nameservers': cf[DEFAULT_NAME_SERVERS],
      'cidr': cidr,
      'network_id': net.id
    }

    if 'dhcp' in attrs: args['is_dhcp_enabled'] = bool(attrs['dhcp'])
    if 'dns_servers' in attrs: args['dns_nameservers'] = attrs['dns_servers']

    snx = c.network.create_subnet(**args)
    print('Created subnet {}'.format(name))
    c.network.add_interface_to_router(vpc, snx.id)
    print('Connected subnet {} to vpc {}'.format(name,vpcname))


  else:
    args = {}
    if 'cidr' in attrs:
      if snx['cidr'] != attrs['cidr']:
        # args['cidr'] = attrs['cidr']
        print('subnet {name} cannot change CIDR on-line to {new} (was {old})'.format(name=name,new=attrs['cidr'],old=snx['cidr']))
    if 'dhcp' in attrs:
      if bool(snx['is_dhcp_enabled']) != bool(attrs['dhcp']):
        # args['is_dhcp_enabled'] = bool(attrs['dhcp'])
        print('subnet {name} cannot change DHCP on-line to {new} (was {old})'.format(name=name,new=attrs['dhcp'],old=snx['is_dhcp_enabled']))
    if 'dns_servers' in attrs:
      if yaml.dump(snx['dns_nameservers']) != yaml.dump(attrs['dns_servers']):
        args['dns_nameservers'] = attrs['dns_servers']
    if len(args) > 0:
        if dryrun:
          print('subnet {} needs to reconfiguration:'.format(name))
          print(args)
        else:
          c.network.update_subnet(snx,**args)
          print('Updated subnet {}:'.format(name))
          print(args)

  return net


def has_eip(server):
  if 'addresses' in server:
    for sn in server['addresses']:
      for ip in server['addresses'][sn]:
        if 'OS-EXT-IPS:type' in ip:
          if ip['OS-EXT-IPS:type'] == 'floating':
            return ip['addr']
  return None

def new_srv(id_or_name,forced_net=None,dryrun=True,**kw):
  c = cf[CLOUD]
  sid = cf[SID]

  name = gen_name(id_or_name,'vm')
  args = { "name": name }

  if 'image' in kw:
    image_name = kw['image']
  else:
    image_name = cf[DEFAULT_IMAGE]
  image = c.compute.find_image(image_name)
  if not image:
    print('Image {image} not found for vm {name}'.format(name=name,image=image_name))
    return None
  args['image_id'] = image.id

  if 'flavor' in kw:
    flavor_name = kw['flavor']
  else:
    favor_name = cf[DEFAULT_FLAVOR]
  flavor = c.compute.find_flavor(flavor_name)
  if not flavor:
    print('Flavor {flavor} not found for vm {name}'.format(name=name,flavor=flavor_name))
    return None
  args['flavor_id'] = flavor.id

  if 'sg' in kw:
    if isinstance(kw['sg'],str):
      # This is a sg name...
      sg_name = '{}-sg-{}'.format(sid,kw['sg'])
      sg = c.network.find_security_group(sg_name)
      if sg is None:
        sg = c.network.find_security_group(kw['sg'])
        if sg is None:
          print('Security group {sg} does not exist for vm {name}'.format(name=name,sg=kw['sg']))
          return None
        sg_name = kw['sg']
    else: # Assume is a list of rules...
      sg_name = gen_name(id_or_name, 'sgvm')
      new_sg(sg_name,  kw['sg'], dryrun=dryrun)
    args['security_groups'] = [{'name': sg_name }]
  else:
    args['security_groups'] = []  # Does this make sense?

  if 'keypair' in kw:
    args['key_name'] = kw['keypair']

  args['networks'] = []
  if forced_net: args['networks'].append({'uuid': forced_net.id})

  if 'nets' in kw:
    if isinstance(kw['nets'],str):
      nets = [ kw['nets'] ]
    else:
      nets = kw['nets']

    for cnet in nets:
      if isinstance(cnet,int):
        netname = '{sid}-sn{nid}'.format(sid = sid, nid = cnet)
      else:
        netname = '{}-{}'.format(sid,cnet)
      net = c.network.find_network(netname)
      if not net:
        print('Network {net} not found for vm {name}'.format(name=name,net=netname))
        return None
      args['networks'].append({'uuid': net.id})
  if len(args['networks']) == 0:
    print('vm {name} is not connected to any network'.format(name=name))
    return None

  if 'user_file' in kw:
    content = ''
    with open(kw['user_file']) as f:
      content = f.read()
    args['user_data'] = base64.b64encode(content.encode('utf-8')).decode('ascii')
  elif 'user_data' in kw:
    if isinstance(kw['user_data'],str):
      args['user_data'] = base64.b64encode(kw['user_data'].encode('utf-8')).decode('ascii')
    else:
      txt = "#cloud-config\n"
      txt += yaml.dump(kw['user_data'])
      args['user_data'] = base64.b64encode(txt.encode('utf-8')).decode('ascii')

  server = c.compute.find_server(name)
  if not server:
    server = c.compute.create_server(**args)
    server = c.compute.wait_for_server(server)
    print('Created server {}'.format(args['name']))
  else:
    server = c.compute.get_server(server)

    nc = {}
    oc = {}
    for k in args:
      nc[k] = args[k]
      if k in server: oc[k] = server[k]

    nc['flavor_id'] = None
    nc['flavor_name'] = flavor_name
    oc['flavor_name'] = server['flavor']['original_name']
    oc['image_id'] = server['image']['id']
    nc['networks'] = None # Note, we don't get this right!

    if yaml.dump(nc) != yaml.dump(oc):
      if dryrun:
        print('WONT recreate vm {} settings changing'.format(name))
        print(args)
      else:
        # We destroy the server and re-create it...
        c.compute.delete_server(server['id'])
        c.compute.wait_for_delete(server)
        print('Deleted vm {}'.format(name))
        server = c.compute.create_server(**args)
        server = c.compute.wait_for_server(server)
        print('Created server {}'.format(args['name']))

  # update internal DNS zone...
  rrs = { 'A': [], 'AAAA': [] }
  for sn in server['addresses']:
    for ip in server['addresses'][sn]:
      if ip['OS-EXT-IPS:type'] == 'fixed' and 'addr' in ip:
        if ip['version'] == 6:
          rrs['AAAA'].append(ip['addr'])
        else:
          rrs['A'].append(ip['addr'])

  for rtype in rrs:
    new_dns('{}.{}'.format(sid,cf[DEFAULT_PRIVATE_DNS_ZONE]), 'private', name, rtype, rrs[rtype], dryrun=dryrun)


  if 'eip' in kw:
    if 'update_dns' in kw:
      upd_dns = kw['update_dns']
    else:
      upd_dns = True

    dns_name = '{}.{}'.format(name,cf[DEFAULT_PUBLIC_DNS_ZONE])

    if kw['eip']:
      # TODO: add support for IPv6
      ip_addr = has_eip(server)
      if not ip_addr:
        eip = c.create_floating_ip(server = server)
        print('Created floating IP for server {}'.format(name))
        ip_addr = eip.floating_ip_address
      if upd_dns:
        new_dns(cf[DEFAULT_PUBLIC_DNS_ZONE], 'public', name, 'A', [ ip_addr ], dryrun=dryrun)
      else:
        del_dns(cf[DEFAULT_PUBLIC_DNS_ZONE], 'public', name, 'A', dryrun=dryrun)
    else:
      if has_eip(server):
        port_ids = {}
        i = 0
        for interface in c.compute.server_interfaces(server):
          port_ids[interface['port_id']] = '{server}-if{port}'.format(server = name, port = i)
          ++i

        for ip in c.network.ips():
          if ip.port_id in port_ids:
            if dryrun:
              print('WONT release IP {ip} from server port {port}'.format(ip=ip.floating_ip_address, port = port_ids[ip.port_id]))
            else:
              c.network.delete_ip(ip)
              print('Released IP {ip} from server port {port}'.format(ip=ip.floating_ip_address, port = port_ids[ip.port_id]))
              del_dns(cf[DEFAULT_PUBLIC_DNS_ZONE], 'public', name, 'A', dryrun=dryrun)

    if upd_dns and ('cname' in kw):
      if isinstance(kw['cname'],str):
        cnames = [ kw['cname'] ]
      else:
        cnames = kw['cname']

      for cn in cnames:
        new_dns(cf[DEFAULT_PUBLIC_DNS_ZONE], 'public', cn, 'CNAME', [ dns_name ], dryrun=dryrun)

  # create and attach volumes
  if 'vols' in kw:
    v_x = {}
    for v_id_or_name in kw['vols']:
      if isinstance(v_id_or_name,str):
        v = find_volume(c, v_id_or_name)
        if not v is None:
          v_x[v['id']] = v
          continue
      vol_name = gen_name(v_id_or_name, name[len(sid)+1:]+'-v')
      v = new_vol(vol_name, dryrun=dryrun, **kw['vols'][v_id_or_name])
      if not v is None:
        v_x[v['id']] = v

    root_device = server['root_device_name']
    for av in server['attached_volumes']:
      avd = c.compute.get_volume_attachment(av['id'],server)
      if avd['device'] == root_device: continue # We skip the root device
      v = avd['volume_id']
      if v in v_x:
        # Already been attached, so remove it from the list...
        del(v_x[v])
      else:
        # We don't know about this volume
        xvol = find_volume(c, v)
        if dryrun:
          print('WONT detach volume {} from vm {}'.format(xvol['name'], name))
        else:
          c.compute.delete_volume_attachment(av['id'],server)
          c.block_store.wait_for_status(xvol,
                                    status='in-use',
                                    failures=['error'],
                                    interval=5,
                                    wait=120)
          print('Detached volume {} from vm {}'.format(xvol['name'], name))

    # Attaching any remaining volumes...
    for v in v_x:
      c.compute.create_volume_attachment(server, volume_id=v_x[v]['id'])
      c.block_store.wait_for_status(v_x[v],
                                    status='in-use',
                                    failures=['error'],
                                    interval=5,
                                    wait=120)
      print('Attached volume {} to vm {}'.format(v_x[v]['name'],name))
  return server



