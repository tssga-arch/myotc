#!/usr/bin/env python3
'''
Create new resources

'''
import yaml
import base64
import consts as K
import myotc

SG_KEYS = ('remote_ip_prefix', 'protocol', 'port_range_min', 'port_range_max' )
SG_COPYKEYS = ('remote_ip_prefix', 'protocol', 'port_range_min', 'port_range_max', 'ethertype', 'remote_ip_prefix' )

def find_volume(c, vname):
  ''' Find volume

  :param openstack.connection c: OpenStack connection
  :param str vname: Resource name
  :returns None|openstack.volume: None if error else volume instance
  '''

  for v in c.block_store.volumes():
    if 'name' in v:
      if v['name'] == vname: return v
    if 'id' in v:
      if v['id'] == vname: return v
  return None

def new_vol(vol_name, opts, **kw):
  ''' Deploy new volume

  :param str vol_name: name of volume
  :param dict opts: session options
  :param kwargs kw: dict for incoming keywoard arguments, containing VM attributes
  :returns None|instance: Returns None on error, volume instance on success

  '''

  c = opts[K.CONN]
  sid = opts[K.SID]
  dryrun = opts[K.DRYRUN]

  cvol = find_volume(c, vol_name)
  if cvol is None:
    # Make sure size is there...
    if not 'size' in kw:
      print('Unable to create volume {}. "size" not specified'.format(vol_name))
      return None

    myotc.msg('Creating volume {}...'.format(vol_name))
    cvol = c.block_store.create_volume(name=vol_name, **kw)
    c.block_store.wait_for_status(cvol,
                                  status='available',
                                  failures=['error'],
                                  interval=5,

                                  wait=120)
    myotc.msg('DONE\n')
  else:
    if cvol['size'] != kw['size']:
      # Volume has been resized...
      if int(kw['size']) < int(cvol['size']):
        print('Not possible to reduce size of volume {}'.format(vol_name))
        return cvol
      myotc.msg('Resizing volume {}...'.format(vol_name))
      cvol.extend(c.block_store, int(kw['size']))
      myotc.msg('DONE\n')
  return cvol

def flatten_rules(rule_lst):
  ''' Convert list of Security Group rules to a string

  :param list rule_list: list of rules to be flatten
  :returns str: string represetnation of ``rule_list``.

  Convert ``rule_list`` to a ``str`` so we can easily compare it.
  '''
  ol = []
  for i in rule_lst:
    ol.append(yaml.dump(i))
  ol.sort()
  return yaml.dump(ol)

def new_sg(sg_name, rule_list, opts):
  ''' Create Security Group

  :param str sg_name: Security group name
  :param list rule_list: List containing security rules
  :param dict opts: Current session options
  :returns security-group-instance: Returns instance to opentstack Security Group
  '''
  c = opts[K.CONN]
  sid = opts[K.SID]
  dryrun = opts[K.DRYRUN]

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
      myotc.msg('Flusing SG {sgname}...'.format(sgname=sg_name))
      for osr in sg['security_group_rules']:
        if osr['direction'] != 'ingress': continue # we only know how to deal with ingress rules
        c.network.delete_security_group_rule(osr)
        cnt += 1
      myotc.msg('Rules flushed: {count}'.format(count=cnt))
  else:
    myotc.msg('Creating SG {}...'.format(sg_name))
    sg = c.network.create_security_group(name = sg_name)
    myotc.msg('DONE\n')

  myotc.msg('SG {sgname} adding rules...'.format(sgname=sg_name))
  cnt = 0
  for rule in rules:
    rule['security_group_id'] = sg.id
    # ~ print(rule)
    c.network.create_security_group_rule(**rule)
    cnt += 1
  myotc.msg('Rules added: {count}\n'.format(sgname=sg_name, count=cnt))

  return sg

def new_vpc(opts, **attrs):
  ''' Create a new VPC

  :param dict opts: dict containing current deployment settings
  :param kwargs attrs: dict for incoming keywoard arguments, containing VPC attributes

  The following attributes are recongized:

  - ``bool snat``: Enable Source NAT
  '''
  c = opts[K.CONN]
  sid = opts[K.SID]
  dryrun = opts[K.DRYRUN]

  vpcname = '{}-vpc1'.format(sid)
  vpc = c.network.find_router(vpcname)
  if not vpc:
    myotc.msg('Creating vpc {}...'.format(vpcname))
    vpc = c.network.create_router(name=vpcname)

    if K.snat in attrs:
      snat = attrs[K.snat]
    else:
      snat = True

    vpc = c.network.update_router(vpc.id,
        external_gateway_info = {
          'enable_snat': snat,
          'network_id': vpc['external_gateway_info']['network_id']
        }
    )
    myotc.msg('DONE\n')
  else:
    if K.snat in attrs:
      snat = bool(attrs[K.snat])
      if bool(vpc['external_gateway_info']['enable_snat']) != snat:
        if dryrun:
          print('vpc {} needs to change snat setting to {}'.format(vpcname,snat))
        else:
          myotc.msg('vpc {} changing snat setting to {}...'.format(vpcname,snat))

          vpc = c.network.update_router(vpc.id,
              external_gateway_info = {
                'enable_snat': snat,
                'network_id': vpc['external_gateway_info']['network_id']
              }
          )
          myotc.msg('DONE\n')

  # Always create an internal dnz zone
  if K.PRIVATE_DNS_ZONE in opts and not opts[K.PRIVATE_DNS_ZONE] is None:
    zname = '{}.{}'.format(sid,opts[K.PRIVATE_DNS_ZONE])
    idnsz = c.dns.find_zone(zname,zone_type=K.private)
    if not idnsz:
      myotc.msg('Creating internal DNS zone {}...'.format(zname))
      idnsz = c.dns.create_zone(
        name=zname,
        router = { K.router_id: vpc.id },
        zone_type=K.private
      )
      myotc.msg('DONE\n')
  else:
    print('No PRIVATE_DNS_ZONE defined')
  return vpc

def flatten_rs(lst):
  ''' Flatten DNS resource records

  :param list lst: Resource record list

  Flatten DNS record sets so that it can be compared
  '''
  r = list(lst)
  r.sort()
  return yaml.dump(r)

def find_rrs(zn,rtype,name, c):
  ''' Find DNS Resource Records

  :param openstack.dnszone zn: OpenStack DNS Zone to query
  :param str rtype: Resource type being queried
  :param str name: Resource name
  :param openstack.connection c: OpenStack connection
  :returns None|RecordSet: None if error, list of resource record sets
  '''

  for rs in c.dns.recordsets(zn):
    if ('name' in rs) and ('type' in rs):
      if rs['name'] == name and rs['type'] == rtype:
        return rs
  return None

def del_dns(zname, zone_type, bsname, rtype, opts):
  ''' Delete DNS records

  :param str zname: zone name to use
  :param str zone_type: Set to 'private' or 'public'
  :param bsname: DNS record name
  :param str rtype: DNS record type, e.g. ``A`` or ``CNAME`` or ``AAAA``, etc.
  :param dict opts: session options

  '''
  c = opts[K.CONN]
  dryrun = opts[K.DRYRUN]

  dnszn = c.dns.find_zone(zname,zone_type=zone_type)
  if not dnszn: return
  name = '{}.{}'.format(bsname,zname)

  cset = find_rrs(dnszn, rtype, name)
  if cset:
    if dryrun:
      print('WONT update DNS {type} record for {name}'.format(type=rtype,name=name))
    else:
      myotc.msg('Deleting DNS {type} record for {name}...'.format(type=rtype,name=name))
      c.dns.delete_recordset(cset,dnszn)
      myotc.msg('DONE\n')

def new_dns(zname, zone_type, bsname, rtype, rrs, opts):
  ''' Create DNS records

  :param str zname: zone name to use
  :param str zone_type: Set to 'private' or 'public'
  :param bsname: DNS record name
  :param str rtype: DNS record type, e.g. ``A`` or ``CNAME`` or ``AAAA``, etc.
  :param list rrs: list of records
  :param dict opts: session options

  '''
  c = opts[K.CONN]
  dryrun = opts[K.DRYRUN]

  dnszn = c.dns.find_zone(zname,zone_type=zone_type)
  if not dnszn: return
  name = '{}.{}'.format(bsname,zname)

  cset = find_rrs(dnszn, rtype, name, c)
  if cset:
    if len(rrs):
      if flatten_rs(cset['records']) != flatten_rs(rrs):
        # So record changed
        if dryrun:
          print('WONT update DNS {type} record for {name}'.format(type=rtype,name=name))
        else:
          myotc.msg('Updating DNS {type} record for {name}...'.format(type=rtype,name=name))
          c.dns.delete_recordset(cset,dnszn)
          c.dns.create_recordset(dnszn, name=name, type = rtype, records = rrs)
          myotc.msg('DONE\n')
    else:
      if dryrun:
        print('WONT delete DNS {type} record for {name}'.format(type=rtype,name=name))
      else:
        myotc.msg('Deleting DNS {type} record for {name}...'.format(type=rtype,name=name))
        c.dns.delete_recordset(cset,dnszn)
        myotc.msg('DONE\n')
  else:
    if len(rrs):
      myotc.msg('Creating DNS {type} record for {name}...'.format(type=rtype,name=name))
      c.dns.create_recordset(dnszn, name=name, type = rtype, records = rrs)
      myotc.msg('DONE\n')


def new_net(id_or_name, opts, cidr_tmpl=None, **attrs):
  ''' Deploy new subnet

  :param int|str id_or_name: base id/name for this subnet
  :param dict opts: session options
  :param cidr_templ: template used to assign CIDR addresses
  :param kwargs attrs: dict for incoming keywoard arguments, containing subnet attributes
  :returns None|instance: Returns None on error, Net instance on success

  '''
  c = opts[K.CONN]
  sid = opts[K.SID]
  dryrun = opts[K.DRYRUN]
  prefix = sid + '-'

  name = myotc.gen_name(id_or_name, 'sn', sid)

  netname = '{}net'.format(name)
  net = c.network.find_network(netname)
  if not net:
    myotc.msg('Creating network {}...'.format(netname))
    net = c.network.create_network(name = netname)
    myotc.msg('DONE\n')

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
          cidr = opts[K.NET_FORMAT].format(id=id_or_name, id_hi=int(id_or_name/256), id_lo=int(id_or_name % 256))
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
      'dns_nameservers': myotc.DEFAULT_NAME_SERVERS,
      'cidr': cidr,
      'network_id': net.id
    }

    if 'dhcp' in attrs: args['is_dhcp_enabled'] = bool(attrs['dhcp'])
    if 'dns_servers' in attrs: args['dns_nameservers'] = attrs['dns_servers']

    myotc.msg('Creating subnet {}...'.format(name))
    snx = c.network.create_subnet(**args)
    myotc.msg('connecting to vpc {}...'.format(vpcname))
    c.network.add_interface_to_router(vpc, snx.id)
    myotc.msg('DONE\n')

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
          myotc.msg('Updating subnet {}:\n'.format(name))
          print(args)
          c.network.update_subnet(snx,**args)
          myotc.msg('DONE\n')

  return net


def has_eip(server):
  ''' Check if server has an floating IP

  :param openstack.server server: OpenStack server instance
  :returns str|None: Returns Floating IP address of server, otherwise returns None
  '''
  if 'addresses' in server:
    for sn in server['addresses']:
      for ip in server['addresses'][sn]:
        if 'OS-EXT-IPS:type' in ip:
          if ip['OS-EXT-IPS:type'] == 'floating':
            return ip['addr']
  return None

def new_srv(id_or_name, opts, **kw):
  ''' Deploy new subnet

  :param int|str id_or_name: base id/name for this subnet
  :param dict opts: session options
  :param kwargs kw: dict for incoming keywoard arguments, containing VM attributes
  :returns None|instance: Returns None on error, VM instance on success
  :todo: Tagging is incomplete

  '''
  c = opts[K.CONN]
  sid = opts[K.SID]
  dryrun = opts[K.DRYRUN]
  prefix = sid + '-'

  name = myotc.gen_name(id_or_name, 'vm', sid)
  args = { "name": name }

  if 'image' in kw:
    image_name = kw['image']
  else:
    image_name = opts[K.DEFAULT_IMAGE]
  image = c.compute.find_image(image_name)
  if not image:
    print('Image {image} not found for vm {name}'.format(name=name,image=image_name))
    return None
  args['image_id'] = image.id

  if 'flavor' in kw:
    flavor_name = kw['flavor']
  else:
    favor_name = cf[K.DEFAULT_FLAVOR]
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
      sg_name = myotc.gen_name(id_or_name, 'sgvm', sid)
      new_sg(sg_name,  kw['sg'], opts)
    args['security_groups'] = [{'name': sg_name }]
  else:
    args['security_groups'] = []  # Does this make sense?

  if 'keypair' in kw:
    args['key_name'] = kw['keypair']

  args['networks'] = []
  if 'forced_net' in kw and not kw['forced_net'] is None: args['networks'].append({'uuid': kw['forced_net'].id})

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
    myotc.msg('Creating server {}...'.format(args['name']))
    server = c.compute.create_server(**args)
    server = c.compute.wait_for_server(server)
    # Tag the server...
    myotc.msg('tagging...')
    server.add_tag(c.compute, 'SID={sid}'.format(sid= sid))
    myotc.msg('DONE\n')
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
        # ~ print(args)
      else:
        # We destroy the server and re-create it...
        myotc.msg('Deleting vm {}...'.format(name))
        c.compute.delete_server(server['id'])
        c.compute.wait_for_delete(server)
        myotc.msg('Re-creating...');
        server = c.compute.create_server(**args)
        server = c.compute.wait_for_server(server)
        myotc.msg('DONE\n')

  if 'image_size' in kw:
    # We may need to resize image volume
    for vid in server['attached_volumes']:
      vdat = c.block_store.get_volume(vid['id'])
      if not 'is_bootable' in vdat: continue
      if not 'volume_image_metadata' in vdat: continue
      if not vdat['is_bootable']: continue
      if not 'image_name' in vdat['volume_image_metadata']: continue
      if vdat['volume_image_metadata']['image_name'] != image_name: continue

      # From here on we consider this volume the boot volume
      if not 'min_disk' in vdat['volume_image_metadata']: break
      if int(kw['image_size']) < int(vdat['volume_image_metadata']['min_disk']):
        print('Ignoring {vname} image_size:{size} < min_disk:{mind}'.format(
              vname = name,
              size = kw['image_size'],
              mind = vdat['volume_image_metadata']['min_disk'],
            ))
        break
      if not 'size' in vdat: break
      if int(kw['image_size']) != int(vdat['size']):
        if int(kw['image_size']) < int(vdat['size']):
            print('Unable resize image volume for {name} from {csize} => {tsize}'.format(
                    name  = name,
                    csize = int(vdat['size']),
                    tsize = int(kw['image_size']),
                  ))
            break
        myotc.msg('Resizing image volume for {name} from {csize} to {tsize}...'.format(
                  name  = name,
                  csize = int(vdat['size']),
                  tsize = int(kw['image_size']),
                ))
        # must resize image volume
        vdat.extend(c.block_store,int(kw['image_size']))
        myotc.msg('DONE\n')

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
    new_dns('{}.{}'.format(sid,opts[K.PRIVATE_DNS_ZONE]), K.private, name, rtype, rrs[rtype], opts)

  if 'eip' in kw:
    if 'update_dns' in kw:
      upd_dns = kw['update_dns']
    else:
      upd_dns = True

    dns_name = '{}.{}'.format(name,opts[K.PUBLIC_DNS_ZONE])

    if kw['eip']:
      # TODO: add support for IPv6
      ip_addr = has_eip(server)
      if not ip_addr:
        myotc.msg('Creating floating IP for server {}...'.format(name))
        eip = c.create_floating_ip(server = server)
        myotc.msg('DONE\n')
        ip_addr = eip.floating_ip_address
      if upd_dns:
        new_dns(opts[K.PUBLIC_DNS_ZONE], K.public, name, 'A', [ ip_addr ], opts)
      else:
        del_dns(opts[K.PUBLIC_DNS_ZONE], K.public, name, 'A', opts)
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
              myotc.msg('Releasing IP {ip} from server port {port}...'.format(ip=ip.floating_ip_address, port = port_ids[ip.port_id]))
              c.network.delete_ip(ip)
              myotc.msg('DONE\n')
              del_dns(opts[K.PUBLIC_DNS_ZONE], K.public, name, 'A', opts)


    if upd_dns and ('cname' in kw):
      if isinstance(kw['cname'],str):
        cnames = [ kw['cname'] ]
      else:
        cnames = kw['cname']

      for cn in cnames:
        new_dns(opts[K.PUBLIC_DNS_ZONE], K.public, cn, 'CNAME', [ dns_name ], opts)

  # create and attach volumes
  if 'vols' in kw:
    v_x = {}
    for v_id_or_name in kw['vols']:
      if isinstance(v_id_or_name,str):
        v = find_volume(c, v_id_or_name)
        if not v is None:
          v_x[v['id']] = v
          continue
      vol_name = myotc.gen_name(v_id_or_name, name[len(sid)+1:]+'-v',sid)
      v = new_vol(vol_name, opts, **kw['vols'][v_id_or_name])
      if not v is None:
        v_x[v['id']] = v

    root_device = server['root_device_name']
    # ~ print(root_device)
    # ~ print(server['attached_volumes'])
    for av in server['attached_volumes']:
      # ~ print(av)
      avd = c.compute.get_volume_attachment(server,av['id'])
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
          myotc.msg('Detaching volume {} from vm {}...'.format(xvol['name'], name))
          c.compute.delete_volume_attachment(av['id'],server)
          c.block_store.wait_for_status(xvol,
                                    status='in-use',
                                    failures=['error'],
                                    interval=5,
                                    wait=120)
          myotc.msg('DONE\n')

    # Attaching any remaining volumes...
    for v in v_x:
      myotc.msg('Attaching volume {} to vm {}...'.format(v_x[v]['name'],name))
      c.compute.create_volume_attachment(server, volume_id=v_x[v]['id'])
      c.block_store.wait_for_status(v_x[v],
                                    status='in-use',
                                    failures=['error'],
                                    interval=5,
                                    wait=120)
      myotc.msg('DONE\n')
  return server



