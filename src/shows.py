#!/usr/bin/env python3
''' Implement the different ways to show openstack objects '''
import yaml
import fnmatch
import os
import time
from datetime import datetime
import ypp # We need this to get configuration data
import myotc
import consts as K

def print_header(header):
  '''Print table header

  :param str header: Formatted header string
  :returns False: Always returns boolean false

  Prints the header as specified.  Then prints a line to underline
  header.
  '''

  print(header)
  txt = ''
  for i in header:
    txt += ' ' if i == ' ' else '='
  print(txt)

def format_2_header(fmt):
  '''Create a header from a format string

  :param str fmt: format string
  :returns str: header string
  '''
  state = 'B'
  fields = []
  hfmt = ''

  for c in fmt:
    if state == 'B':
      hfmt += c
      if c != '{': continue

      state = 'F' # Processing a field name
      fname = ''
    elif state =='F':
      if c == '}':
        hfmt += c
        fields.append(fname)
        state = 'B'
      elif c == ':':
        hfmt += c
        fields.append(fname)
        state = 'O'
        opts = ''
      else:
        fname += c
    elif state =='O':
      if c =='}':
        if opts[0] == '-': opts = opts[1:]
        if opts[-1] == ',' or opts[-1] == '_': opts = opts[:-1]
        hfmt += opts
        hfmt += c
        state = 'B'
      else:
        opts += c

  return hfmt.format(*fields)

def vmlist_cmd(args):
  '''Show VM list

  :param namespace args: values from CLI parser
  '''
  first = True

  if 'cfgopts' in args:
    c = args.cfgopts[K.CONN]
    args.spec.append(args.cfgopts[K.NAME])
    prefix = None
  else:
    c = myotc.connect(args)
    if args.sid:
      prefix = '{}-'.format(args.sid)
    elif not ypp.vars(K.SID) is None:
      prefix = '{}-'.format(ypp.vars(K.SID))
    else:
      prefix = None

  xtab = {K.image_id: K.sID, K.image_size: K.size, K.image_name: K.NAME }
  if args.format:
    fmt = args.format
    hdr = format_2_header(fmt)
  else:
    hdr = '{:16} {:5} {:>10} {:8} {}'.format('name','vcpus','ram','status','ip, uptime, image')
    fmt = '{name:16} {vcpus:5} {ram:10,} {status:8} {ipv4} [{updated_ago}]\n                                           {image_name}'

  lookup_img = '{image_' in fmt

  for vm in c.compute.servers():
    if K.NAME in vm:
      if prefix:
        if not vm[K.NAME].startswith(prefix): continue
      if len(args.spec):
        match = False
        for wc in args.spec:
          if fnmatch.fnmatch(vm[K.NAME],wc):
            match = True
            break
        if not match: continue

    if args.details:
      print(ypp.dump([dict(vm)]))

      # ~ for vol in vm['attached_volumes']:
        # ~ pprint(vol)
        # ~ vol = c.compute.get_volume_attachment(vol['id'],vm)
        # ~ pprint(vol)
        # ~ cvol = c.get_volume(vol['volume_id'])
        # ~ pprint(cvol)
    else:
      t = dict(vm)
      if lookup_img and K.image in t and K.sID in t[K.image]:
        i = dict(c.image.get_image(vm.image.id))
        for k in xtab:
          t[k] = i[xtab[k]]

      if K.addresses in t:
        t[K.ipv4] = []
        t[K.mac] = {}
        t[K.nets] = []
        for netid in t[K.addresses]:
          t[K.nets].append(netid)
          for a in t[K.addresses][netid]:
            if K.OS_EXT_IPS_MAC_ADDR in a:
              t[K.mac][a[K.OS_EXT_IPS_MAC_ADDR]] = a[K.OS_EXT_IPS_MAC_ADDR]
            t[K.ipv4].append('{addr} ({type})'.format(addr=a[K.addr],type=a[K.OS_EXT_IPS_TYPE]))
        t[K.ipv4] = ', '.join(t[K.ipv4])
        t[K.mac] =', '.join(t[K.mac])
        t[K.nets] = ', '.join(t[K.nets])
      if K.flavor in t:
        t[K.vcpus] = t[K.flavor][K.vcpus]
        t[K.ram] = t[K.flavor][K.ram]
        t[K.flavor_name] = t[K.flavor][K.original_name]
      for ts in (K.created_at,K.launched_at,K.updated_at):
        if not ts in t: continue
        if t[ts] is None: continue
        if t[ts].endswith('Z'):
          t[ts] = t[ts][:-1] + "+00:00"
        nk = ts[:-3] + "_ago"
        tt = int(time.time() - datetime.fromisoformat(t[ts]).timestamp())
        if tt > 86400:
          i = int(tt / 86400)
          if i == 1:
            txt = 'one day'
          else:
            txt = '{:,} days'.format(i)
        elif tt > 3600:
          i = int(tt/3600)
          if i == 1:
            txt = 'one hour'
          else:
            txt = '{} hours'.format(i)
        elif tt > 60:
          i = int(tt/60)
          if i == 1:
            txt = 'one minute'
          else:
            txt = '{} minutes'.format(i)
        else:
          txt = 'a few seconds'
        txt = txt + ' ago'
        t[nk] = txt

        # ~ print('%s -> %s' % (nk,txt))

      # ~ pprint(t)

      if first: first = print_header(hdr)
      print(fmt.format(**t))

def lists_cmd(args):
  '''Implement different lists

  :param namespace args: values from CLI parser

  This function supports:

  * vpc
  * key
  * net
  * zone
  * sgs
  * vols

  '''
  c = myotc.connect(args)
  fmt = args.format
  hdr = None

  if args.mode == K.vpc:
    if K.USE_OTC_API:
      if fmt is None:
        fmt = '{name:20} {snat:4} {cidr}'
        hdr = '{:20} {:4} {}'.format('name','snat','CIDR')
      iterator = []
      for vpc in c.vpc.vpcs():
        k = dict(vpc)
        k[K.snat] = 'Yes' if k['enable_shared_snat'] else 'No'
        if k['cidr'] is None: k['cidr'] = 'None'
        iterator.append(k)
      
    else:
      if fmt is None:
        fmt = '{name:20} {status}'
        hdr = '{:20} {}'.format('name','status')
      iterator = c.network.routers()
      
  elif args.mode == K.key:
    if fmt is None:
      fmt = '{name:16} {type:8} {short_public_key}'
      hdr = '{:16} {:8} {}'.format('name','type','public key')

    iterator = []
    for k in c.compute.keypairs():
      k = dict(k)
      if K.public_key in k:
        skn = k[K.public_key].split()
        if len(skn[1]) > 25:
          skn[1] = skn[1][0:10] + " ... " + skn[1][-10:]
        k[K.short_public_key] = ' '.join(skn)
      iterator.append(k)
  elif args.mode == K.net:
    if fmt is None:
      fmt = '{name:16} {cidr:16}'
      hdr = '{:16} {:16}'.format('name','CIDR')

    iterator = []
    for net in c.network.networks():
      for snid in net[K.subnet_ids]:
        snet = c.network.find_subnet(snid)
        if snet is None: continue

        sndat = dict(snet)
        sndat[K.net_data] = dict(net)
        xtab = {K.NAME: K.net_name, K.sID: K.net_id,
                  K.availability_zones: K.net_az,
                  K.dns_domain: K.net_dns_domain}
        for kp in xtab:
          if kp in net: sndat[xtab[kp]] = net[kp]
        iterator.append(sndat)
  elif args.mode == K.zone:
    if fmt is None:
      fmt = '{name:24} {zone_type:8} {record_num:3}'
      hdr = '{:24} {:8} {:3}'.format('name','type','rrs')

    iterator = []
    for z in c.dns.zones():
      iterator.append(dict(z))
    for z in c.dns.zones(zone_type=K.private):
      iterator.append(dict(z))
  elif args.mode == K.sgs:
    if fmt is None:
      fmt = '{name:18} {rules:-3}'
      hdr = '{:18} {}'.format('name','#rules')

    iterator = []
    for sg in c.network.security_groups():
      sg = dict(sg)
      if K.security_group_rules in sg:
        sg[K.rules] = len(sg[K.security_group_rules])
      else:
        sg[K.rules] = 0
      iterator.append(sg)
  elif args.mode == K.vols:
    if fmt is None:
      fmt = '{name:16} {size:8,} {status:12} {vm}:{vm_device}'
      hdr = '{:16} {:>8} {:12} {}'.format('name','size','status','vm')

    iterator = []
    for z in c.block_store.volumes():
      q = dict(z)
      q[K.vm] = None
      q[K.vm_device] = None
      if K.attachments in q:
        if isinstance(q[K.attachments],list):
          for n in q[K.attachments]:
            s = c.compute.find_server(n[K.server_id])
            if not s is None:
              q[K.vm] = s[K.NAME]
              q[K.vm_device] = n[K.device]
              break
      iterator.append(q)
  else:
    print('Invalid mode: {}'.format(args.mode))

  first = True
  if hdr is None: hdr = format_2_header(fmt)

  for obj in iterator:
    if not K.NAME in obj: continue
    if len(args.spec):
      match = False
      for wc in args.spec:
        if fnmatch.fnmatch(obj[K.NAME],wc):
          match = True
          break
      if not match: continue
    if args.details:
      t = dict(obj)
      print(ypp.dump([t]))
    else:
      if first: first = print_header(hdr)
      print(fmt.format(**obj))

def check_cache(cache_file):
  ''' Check if data was chached

  :param str cache_file: cache file name
  :returns None|mixed: Returns None if cache is invalid, otherwise returns cached data

  Some data requests can be quite large, so they are cached.  The cache
  file is valid for 1 day and is stored in YAML format.
  '''


  if os.path.isfile(cache_file):
    tm = os.path.getmtime(cache_file)
    if int(time.time()) - tm < 86400:
      with open(cache_file,'r') as fp:
        yc = ypp.load(fp)
        return yc
  return None

def save_cache(cache_file, data):
  '''Save the retrieved ``data`` to a cache file

  :param str cache_file: cache file name
  :param list data: list of dictionaries containing data
  :returns list: containing the saved data

  The data is supposed to contain a list of dictionaries.  Each
  dictionary element must always contain a ``name`` attribute
  to be recognized.
  '''

  saved = []
  for i in data:
    if not K.NAME in i: continue
    i = dict(i)
    if K.location in i: del i[K.location]
    saved.append(i)
  with open(cache_file, 'w') as fp:
    fp.write(ypp.dump(saved))
  return saved


def imgs_cmd(args):
  '''List Operating System images

  :param namespace args: values from CLI parser

  '''
  cache_file = K.imglst_yaml

  imgs = check_cache(cache_file)
  if imgs is None:
    c = myotc.connect(args)
    imgs = save_cache(cache_file, c.image.images())

  first = True
  if args.format:
    fmt = args.format
    hdr = format_2_header(fmt)
  else:
    fmt = '{id:36} {name}'
    hdr = '{:36} {}'.format('id','name')
  for img in imgs:
    if len(args.spec):
      match = False
      for wc in args.spec:
        if fnmatch.fnmatch(img[K.NAME],wc):
          match = True
          break
      if not match: continue
    if args.details:
      print(ypp.dump([dict(img)]))
    else:
      if first: first = print_header(hdr)
      print(fmt.format(**img))


def flavors_cmd(args):
  '''List VM flavors

  :param namespace args: values from CLI parser
  '''
  cache_file = K.flavorlst_yaml

  flavors = check_cache(cache_file)
  if flavors is None:
    c = myotc.connect(args)
    flavors = save_cache(cache_file, c.compute.flavors(True))

  if args.cpu:
    args.min_cpu = args.cpu
    args.max_cpu = args.cpu
  if args.mem:
    args.min_mem = args.mem
    args.max_mem = args.mem

  first = True
  if args.format:
    fmt = args.format
    hdr = format_2_header(fmt)
  else:
    fmt = '{name:20} {vcpus:5} {ram:10,}'
    hdr = '{:20} {:5} {:>10}'.format('name','vcpus','ram')

  for flavor in flavors:
    if len(args.spec):
      match = False
      for wc in args.spec:
        if fnmatch.fnmatch(flavor[K.NAME],wc):
          match = True
          break
      if not match: continue
    if args.min_cpu and flavor[K.vcpus] < args.min_cpu: continue
    if args.max_cpu and args.max_cpu < flavor[K.vcpus]: continue
    if args.min_mem and flavor[K.ram] < args.min_mem: continue
    if args.max_mem and args.max_mem < flavor[K.ram]: continue

    if args.details:
      print(ypp.dump([dict(flavor)]))
    else:
      if first: first = print_header(hdr)
      print(fmt.format(**flavor))
