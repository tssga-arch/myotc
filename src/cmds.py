#!/usr/bin/env python3
''' Most command implementation entry points '''
import sys
import fnmatch
import ypp
import nukes
import deploy
import myotc
import consts as K
import os

def sort_vms(vmlist):
  '''Sort VMs according to dependancies

  :param dict vmlist: dict of dict containing VM definitions
  :returns list: list containing vmids in the right ordered
  :todo: untested

  It will look in the VM defitions for the ``reqs`` key, containing
  a list of vmid's that the VM depends on.

  '''
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


def resolv_yaml(yc):
  '''Resolve YAML file VM dependancies

  :param dict yc: dict containing YAML OTC configuration
  :returns list: returns a list of ordered VMs.
  '''
  sid = ypp.vars(K.SID)
  if sid is None:
    myotc.msg('Must specify a SID\n')
    sys.exit(1)
  if not K.nets in yc:
    myotc.msg('No networks defined\n')
    sys.exit(1)

  vmqueue = {}

  for net_id in yc[K.nets]:
    if K.vms in yc[K.nets][net_id]:
      for vmid in yc[K.nets][net_id][K.vms]:
        vmqueue[vmid] = yc[K.nets][net_id][K.vms][vmid]

  if K.vms in yc:
    for vmid in yc[K.vms]:
      vmqueue[vmid] = yc[K.vms][vmid]

  vmorder = []
  for i in sort_vms(vmqueue):
    vmorder.append(myotc.gen_name(i,K.vm,sid))

  return vmorder


def deploy_cmd(args):
  '''deploy command: deploy environment on OTC

  :param namespace args: values from CLI parser
  '''
  dryrun = not args.execute
  yc = ypp.process(args.file, args.include, args.define)

  sid = ypp.vars(K.SID)
  if sid is None:
    myotc.msg('Must specify a SID\n')
    sys.exit(1)
  if not K.nets in yc:
    print('No networks defined')
    sys.exit(1)

  c = myotc.connect(args)
  opts = {
    K.CONN: c,
    K.SID: sid,
    K.DRYRUN: dryrun,
    K.PRIVATE_DNS_ZONE: ypp.vars(K.PRIVATE_DNS_ZONE, K.DEFAULT_PRIVATE_DNS_ZONE),
    K.PUBLIC_DNS_ZONE:  ypp.vars(K.PUBLIC_DNS_ZONE),
    K.CIDR_BLOCK: ypp.vars(K.CIDR_BLOCK, K.DEFAULT_CIDR_BLOCK),
    K.DEFAULT_FLAVOR: ypp.vars(K.DEFAULT_FLAVOR, K.DEFAULT_FLAVOR_VAL),
    K.DEFAULT_IMAGE: ypp.vars(K.DEFAULT_IMAGE, K.DEFAULT_IMAGE_VAL),
  }
  snat = True if not K.snat in yc else yc[K.snat]
  deploy.new_vpc(opts, snat=snat)

  if K.sgs in yc:
    # Create shareble security groups
    for sgn in yc[K.sgs]:
      deploy.new_sg('{}-sg-{}'.format(sid,sgn),yc[K.sgs][sgn],opts)

  vmqueue = {}

  for net_id in yc[K.nets]:
    net = deploy.new_net(net_id,opts,**yc[K.nets][net_id])

    # create vms in net...
    if K.vms in yc[K.nets][net_id]:
      for vmid in yc[K.nets][net_id][K.vms]:
        vm = dict(yc[K.nets][net_id][K.vms][vmid])
        vm[K.forced_net] = net
        vmqueue[vmid] = vm

  if K.vms in yc:
    for vmid in yc[K.vms]:
      vm = dict(yc[K.nets][net_id][K.vms][vmid])
      vmqueue[vmid] = vm

  vmorder = sort_vms(vmqueue)
  for vmid in vmorder:
    deploy.new_srv(vmid, opts, **vmqueue[vmid])

def nuke_cmd(args):
  '''nuke command: destroy a deployed environment

  :param namespace args: values from CLI parser
  '''
  if not args.file is None:
    ypp.process(args.file, args.include, args.define)
  else:
    ypp.yaml_init(args.include,args.define)

  sid = ypp.vars(K.SID)
  if sid is None:
    myotc.msg('Must specify a SID\n')
    sys.exit(1)

  c = myotc.connect(args)

  nukes.nuke(c, sid, args.execute,
        ypp.vars(K.PRIVATE_DNS_ZONE, K.DEFAULT_PRIVATE_DNS_ZONE),
        ypp.vars(K.PUBLIC_DNS_ZONE))

def ping_cmd(args):
  '''Check if things are configured properly

  :param namespace args: values from CLI parser
  '''
  c = myotc.connect(args)

  out = c.get_external_ipv4_networks()
  if args.output: myotc.pprint(out)
  out = c.get_external_ipv6_networks()
  if args.output: myotc.pprint(out)

def resolv_cmd(args):
  '''Resolve Command Line entry point

  :param namespace args: values from CLI parser
  '''

  yc = ypp.process(args.file, args.include, args.define)

  vmorder = resolv_yaml(yc)
  if args.reverse: vmorder.reverse()

  for i in vmorder: print(i)

def conout_cmd(args):
  ''' Show a VM's console output

  :param namespace args: values from CLI parser
  '''
  c = myotc.connect(args)

  for vmname in args.name:
    srv = c.compute.find_server(vmname)
    srv = c.compute.get_server(srv)
    data = c.compute.get_server_console_output(srv,length=20)
    if len(args.name) > 1:
      print('{}\n==='.format(args.name))
    if args.yaml or (not 'output' in data):
      print(ypp.dump(data))
    else:
      print(data['output'])

def state_cmd(args):
  '''Change VM state (stop. start, reboot)

  :param namespace args: values from CLI parser
  '''
  if 'cfgopts' in args:
    c = args.cfgopts[K.CONN]
    vmorder = [ args.cfgopts[K.NAME] ]
  else:
    c = myotc.connect(args)
    if 'file' in args and args.file:
      yc = ypp.process(args.file, args.include, args.define)
      vmorder = resolv_yaml(yc)
      if args.mode == K.stop: vmorder.reverse()
    else:
      vmorder = []
      for i in c.compute.servers():
        if not K.NAME in i: continue
        vmorder.append(i[K.NAME])

      if len(args.name) == 0:
        print('Must provide a list of VMs')
        sys.exit(2)

  for vmname in vmorder:
    if 'name' in args and len(args.name):
      match = False
      for wc in args.name:
        if fnmatch.fnmatch(vmname,wc):
          match = True
          break
      if not match: continue

    srv = c.compute.find_server(vmname)
    if srv is None:
      print('VM {vmname} not defined'.format(vmname=vmname))
      continue
    srv = c.compute.get_server(srv)
    if not K.status in srv:
      print('Unable to determine VM status for {vmname}'.format(vmname=vmname))
      continue
    if args.mode == K.start:
      if srv[K.status] != K.ACTIVE:
        myotc.msg('Starting vm {name}...'.format(name=vmname))
        c.compute.start_server(srv)
        srv = c.compute.wait_for_server(srv)
        myotc.msg('DONE\n')
      else:
        myotc.msg('vm {} is already started\n'.format(vmname))
    elif args.mode == K.stop:
      if srv[K.status] != K.SHUTOFF:
        myotc.msg('Stopping vm {name}...'.format(name=vmname))
        c.compute.stop_server(srv)
        srv = c.compute.wait_for_server(srv,status=K.SHUTOFF)
        myotc.msg('DONE\n')
      else:
        myotc.msg('vm {} is already stopped\n'.format(vmname))
    elif args.mode == K.reboot:
      if srv[K.status] == K.ACTIVE:
        if args.forced:
          myotc.msg('HARD booting vm {name}...'.format(name=vmname))
          c.compute.reboot_server(srv,K.HARD)
        else:
          myotc.msg('SOFT booting vm {name}...'.format(name=vmname))
          c.compute.reboot_server(srv,K.SOFT)
          srv = c.compute.wait_for_server(srv,status=K.REBOOT,wait=500)
          srv = c.compute.wait_for_server(srv,status=K.ACTIVE)
        myotc.msg('DONE\n')
      else:
        myotc.msg('vm {} is not in an active state\n'.format(vmname))



def new_vault(args):
  '''Create a new shared secrets store

  :param namespace args: values from CLI parser
  '''
  DIR = '../secrets'
  FILE = DIR + '/_secrets.yaml'

  if not os.path.isdir(DIR):
    if args.debug: print('Creating folder {}'.format(DIR))
    os.mkdir(DIR)
  if not os.path.isfile(FILE):
    if args.debug: print('Creating file {}'.format(FILE))
    with open(FILE, 'w') as fp:
      fp.write('{}\n')

