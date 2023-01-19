#!/usr/bin/env python3
import openstack
import sys
import os

CLOUD = 0
SID = 1
EXTERNAL_NETWORK = 2 #?
DEFAULT_NETWORK = 3 #?

DEFAULT_IMAGE = 4
DEFAULT_FLAVOR = 5
DEFAULT_NAME_SERVERS = 6
DEFAULT_PUBLIC_DNS_ZONE = 7
DEFAULT_PRIVATE_DNS_ZONE = 8
DEFAULT_NET_FORMAT = 9

cf = [
  None, None, None, None,
  'Standard_CentOS_8_latest', 's3.medium.2',
  [ '100.125.4.25', '100.125.129.199' ],
  os.getenv('DEFAULT_PUBLIC_DOMAIN','otc1.cloudkit7.xyz.'),
  'nova.', '10.{id_hi}.{id_lo}.0/24'
]

def defaults(index, value):
  cf[index] = value

def pprint(z):
  cf[CLOUD].pprint(z)

def my_otc(sid = None):
  # ~ print(sys.env["HOME"])
  auth = os.getenv('CLOUD','otc')
  cf[CLOUD] = openstack.connect(cloud=auth)
  cf[SID] = sid
  return cf[CLOUD]

def gen_name(id_or_name, prefix):
  sid = cf[SID]
  if isinstance(id_or_name,int):
    return '{sid}-{prefix}{id}'.format(sid=sid,prefix=prefix,id=id_or_name)
  name = str(id_or_name)
  if name.startswith(sid+'-'):
    return name
  return '{}-{}'.format(sid,name)

#
# Support functions
#
def resolv_yaml(yc):
  if not 'sid' in yc:
    print('Missing "sid" entry')
    sys.exit(1)
  if not 'nets' in yc:
    print('No networks defined')
    sys.exit(1)

  sid = yc['sid']
  cf[SID] = sid

  vmqueue = {}

  for net_id in yc['nets']:
    if 'vms' in yc['nets'][net_id]:
      for vmid in yc['nets'][net_id]['vms']:
        vmqueue[vmid] = yc['nets'][net_id]['vms'][vmid]

  if 'vms' in yc:
    for vmid in yc['vms']:
      vmqueue[vmid] = yc['vms'][vmid]

  vmorder = []
  for i in sort_vms(vmqueue):
    vmorder.append(gen_name(i,'vm'))

  return vmorder

def sort_vms(vmlist):
  vmorder = []
  vmd = {}
  vmq = {}

  for vmid in vmlist:
    vmq[vmid] = vmid
    if 'reqs' in vmlist[vmid]:
      missing = {}
      for rq in vmlist[vmid]['reqs']:
        if not rq in vmlist:
          missing[rq] = rq
      if len(missing) > 0:
        for i in missing:
          print('vm {vmid} requires unknown vm: {i}'.format(vmid=vmid,i=i))

  lres = -1
  while lres != 0:
    lres = 0
    cnt = 0
    for vmid in vmq:
      if vmid in vmd:
        cnt += 1
        continue
      if 'reqs' in vmlist[vmid]:
        ok = True
        for req in vmlist[vmid]['reqs']:
          if not req in vmq: continue # unknown dependancy
          if not req in vmd:
            ok = False
            break
        if not ok: continue
      vmorder.append(vmid)
      vmd[vmid] = vmid
      lres += 1
      cnt += 1

  if lres == 0 and cnt < len(vmq):
    print('Unable to resolve dependancies for:')
    for i in vmq:
      if i in vmd: continue
      print('  - {} ({})'.format(i,str(vmlist[i]['reqs'])))
      vmorder.append(i)

  return vmorder

