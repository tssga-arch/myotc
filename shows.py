#!/usr/bin/env python3
import yaml
import fnmatch
import os
import time
from datetime import datetime

# ~ import openstack
# ~ import sys
# ~ import nukes

import ypp
from cfn import *

def vmlist_cmd(args):
  c = my_otc()
  first = True
  if args.sid:
    prefix = '{}-'.format(args.sid)
  else:
    prefix = None
  for vm in c.compute.servers():
    if 'name' in vm:
      if prefix:
        if not vm['name'].startswith(prefix): continue
      if len(args.spec):
        match = False
        for wc in args.spec:
          if fnmatch.fnmatch(vm['name'],wc):
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
      if 'addresses' in t:
        t['ipv4'] = []
        t['mac'] = {}
        t['nets'] = []
        for netid in t['addresses']:
          t['nets'].append(netid)
          for a in t['addresses'][netid]:
            if 'OS-EXT-IPS-MAC:mac_addr' in a:
              t['mac'][a['OS-EXT-IPS-MAC:mac_addr']] = a['OS-EXT-IPS-MAC:mac_addr']
            t['ipv4'].append('{addr} ({type})'.format(addr=a['addr'],type=a['OS-EXT-IPS:type']))
        t['ipv4'] = ', '.join(t['ipv4'])
        t['mac'] =', '.join(t['mac'])
        t['nets'] = ', '.join(t['nets'])
      if 'flavor' in t:
        t['vcpus'] = t['flavor']['vcpus']
        t['ram'] = t['flavor']['ram']
        t['flavor_name'] = t['flavor']['original_name']
      for ts in ('created_at','launched_at','updated_at'):
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

      if args.format:
        fmt = args.format
      else:
        if first:
          print('{:16} {:5} {:>10} {:8} {}'.format('name','vcpus','ram','status','ip'))
          first = False
        fmt = '{name:16} {vcpus:5} {ram:10,} {status:8} {ipv4} [{updated_ago}]'
      print(fmt.format(**t))

def lists_cmd(args):
  c = my_otc()

  if args.mode == 'vpc':
    iterator = c.network.routers()
  elif args.mode == 'key':
    iterator = []
    for k in c.compute.keypairs():
      k = dict(k)
      if 'public_key' in k:
        skn = k['public_key'].split()
        if len(skn[1]) > 25:
          skn[1] = skn[1][0:10] + " ... " + skn[1][-10:]
        k['short_public_key'] = ' '.join(skn)
      iterator.append(k)
  elif args.mode == 'net':
    iterator = []
    for net in c.network.networks():
      for snid in net['subnet_ids']:
        snet = c.network.find_subnet(snid)
        if snet is None: continue

        sndat = dict(snet)
        sndat['net_data'] = dict(net)
        xtab = {'name': 'net_name', 'id': 'net_id',
                  'availability_zones': 'net_az',
                  'dns_domain': 'net_dns_domain'}
        for kp in xtab:
          if kp in net: sndat[xtab[kp]] = net[kp]
        iterator.append(sndat)
  elif args.mode == 'zone':
    iterator = []
    for z in c.dns.zones():
      iterator.append(dict(z))
    for z in c.dns.zones(zone_type='private'):
      iterator.append(dict(z))
  elif args.mode == 'sgs':
    iterator = c.network.security_groups()
  elif args.mode == 'vols':
    iterator = []
    for z in c.block_store.volumes():
      q = dict(z)
      q['vm'] = None
      q['vm_device'] = None
      if 'attachments' in q:
        if isinstance(q['attachments'],list):
          for n in q['attachments']:
            s = c.compute.find_server(n['server_id'])
            if not s is None:
              q['vm'] = s['name']
              q['vm_device'] = n['device']
              break
      iterator.append(q)
  else:
    print('Invalid mode: {}'.format(args.mode))

  first = True
  for obj in iterator:
    if not 'name' in obj: continue
    if len(args.spec):
      match = False
      for wc in args.spec:
        if fnmatch.fnmatch(obj['name'],wc):
          match = True
          break
      if not match: continue
    if args.details:
      t = dict(obj)
      print(ypp.dump([t]))
    else:
      if first:
        print(args.header)
        first = False
      print(args.format.format(**obj))

def check_cache(cache_file):
  if os.path.isfile(cache_file):
    tm = os.path.getmtime(cache_file)
    if int(time.time()) - tm < 86400:
      with open(cache_file,'r') as fp:
        yc = ypp.load(fp)
        return yc
  return None


def imgs_cmd(args):
  c = my_otc()
  cache_file = 'imglst.yaml'

  imgs = check_cache(cache_file)
  if imgs is None:
    imgs = c.compute.images(True)
    fp = open(cache_file,'w')
  else:
    fp = None

  first = True
  for img in imgs:
    if not 'name' in img: continue
    if fp: fp.write(ypp.dump([dict(img)]))
    if len(args.spec):
      match = False
      for wc in args.spec:
        if fnmatch.fnmatch(img['name'],wc):
          match = True
          break
      if not match: continue
    if args.details:
      print(ypp.dump([dict(img)]))
    else:
      if args.format:
        fmt = args.format
      else:
        if first:
          print('{:36} {}'.format('id','name'))
          first = False
        fmt = '{id:36} {name}'
      print(fmt.format(**img))


def flavors_cmd(args):
  c = my_otc()
  cache_file = 'flavorlst.yaml'

  flavors = check_cache(cache_file)
  if flavors is None:
    flavors = c.compute.flavors(True)
    fp = open(cache_file,'w')
  else:
    fp = None

  if args.cpu:
    args.min_cpu = args.cpu
    args.max_cpu = args.cpu
  if args.mem:
    args.min_mem = args.mem
    args.max_mem = args.mem


  first = True
  for flavor in flavors:
    if not 'name' in flavor: continue
    if fp: fp.write(ypp.dump([dict(flavor)]))
    if len(args.spec):
      match = False
      for wc in args.spec:
        if fnmatch.fnmatch(flavor['name'],wc):
          match = True
          break
      if not match: continue
    if args.min_cpu and flavor['vcpus'] < args.min_cpu: continue
    if args.max_cpu and args.max_cpu < flavor['vcpus']: continue
    if args.min_mem and flavor['ram'] < args.min_mem: continue
    if args.max_mem and args.max_mem < flavor['ram']: continue

    if args.details:
      print(ypp.dump([dict(flavor)]))
    else:
      if args.format:
        fmt = args.format
      else:
        if first:
          print('{:20} {:5} {:>10}'.format('name','vcpus','ram'))
          first = False
        fmt = '{name:20} {vcpus:5} {ram:10,}'
      print(fmt.format(**flavor))
