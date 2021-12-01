#!/usr/bin/env python3
import sys
import fnmatch
import ypp
import nukes
import deploy
from cfn import *

###################################################################
#
# Sub-command implementations
#
###################################################################

def deploy_cmd(args):
  yc = ypp.process(args.file, args.include, args.define)
  if not 'sid' in yc:
    print('Missing "sid" entry')
    sys.exit(1)
  if not 'nets' in yc:
    print('No networks defined')
    sys.exit(1)

  sid = yc['sid']
  my_otc(sid)

  if 'snat' in yc:
    snat = yc['snat']
  else:
    snat = True
  dryrun = not args.execute
  deploy.new_vpc(snat=snat,dryrun=dryrun)

  if 'sgs' in yc:
    # Create shareble security groups
    for sgn in yc['sgs']:
      deploy.new_sg('{}-sg-{}'.format(sid,sgn),yc['sgs'][sgn],dryrun=dryrun)

  vmqueue = {}
  if 'cidr_template' in yc:
    cidr_tmpl = yc['cidr_template']
  else:
    cidr_tmpl = None

  for net_id in yc['nets']:
    net = deploy.new_net(net_id,dryrun=dryrun,cidr_tmpl=cidr_tmpl,**yc['nets'][net_id])

    # create vms in net...
    if 'vms' in yc['nets'][net_id]:
      for vmid in yc['nets'][net_id]['vms']:
        vm = dict(yc['nets'][net_id]['vms'][vmid])
        vm['forced_net'] = net
        vmqueue[vmid] = vm

  if 'vms' in yc:
    for vmid in yc['vms']:
      vm = dict(yc['nets'][net_id]['vms'][vmid])
      vmqueue[vmid] = vm

  vmorder = sort_vms(vmqueue)
  for vmid in vmorder:
    deploy.new_srv(vmid, dryrun=dryrun, **vmqueue[vmid])

def nuke_cmd(args):
  yc = ypp.process(args.file, args.include, args.define)
  if not 'sid' in yc:
    print('Missing "sid" entry')
    sys.exit(1)

  my_otc(yc['sid'])
  nukes.nuke(cf[CLOUD], cf[SID], args.execute,
        cf[DEFAULT_PRIVATE_DNS_ZONE], cf[DEFAULT_PUBLIC_DNS_ZONE])

def ping_cmd(args):
  my_otc()
  c = cf[CLOUD]

  out = c.get_external_ipv4_networks()
  if args.output: pprint(out)
  out = c.get_external_ipv6_networks()
  if args.output: pprint(out)

def resolv_cmd(args):
  yc = ypp.process(args.file, args.include, args.define)

  vmorder = resolv_yaml(yc)
  if args.reverse: vmorder.reverse()

  for i in vmorder: print(i)

def conout_cmd(args):
  c = my_otc()

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
  c = my_otc()

  if args.file:
    yc = ypp.process(args.file, args.include, args.define)
    vmorder = resolv_yaml(yc)
    if args.mode == 'stop': vmorder.reverse()
  else:
    vmorder = []
    for i in c.compute.servers():
      if not 'name' in i: continue
      vmorder.append(i['name'])

    if len(args.name) == 0:
      print('Must provide a list of VMs')
      sys.exit(2)

  for vmname in vmorder:
    if len(args.name):
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
    if not 'status' in srv:
      print('Unable to determine VM status for {vmname}'.format(vmname=vmname))
      continue
    if args.mode == 'start':
      if srv['status'] != 'ACTIVE':
        c.compute.start_server(srv)
        srv = c.compute.wait_for_server(srv)
        print('Started vm {}'.format(vmname))
      else:
        print('vm {} is already started'.format(vmname))
    elif args.mode == 'stop':
      if srv['status'] != 'SHUTOFF':
        c.compute.stop_server(srv)
        srv = c.compute.wait_for_server(srv,status='SHUTOFF')
        print('Stopped vm {}'.format(vmname))
      else:
        print('vm {} is already stopped'.format(vmname))
    elif args.mode == 'reboot':
      if srv['status'] == 'ACTIVE':
        if args.forced:
          c.compute.reboot_server(srv,'HARD')
          print('HARD booting vm {name}'.format(name=vmname))
        else:
          c.compute.reboot_server(srv,'SOFT')
          srv = c.compute.wait_for_server(srv,status='REBOOT',wait=500)
          print('Rebooting vm {name}'.format(name=vmname))
          srv = c.compute.wait_for_server(srv,status='ACTIVE')
          print('Rebooted vm {name}'.format(name=vmname))
      else:
        print('vm {} is not in an active state'.format(vmname))



