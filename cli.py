#!/usr/bin/env python3
import ypp
import shows
import cmds
from cfn import *
from argparse import ArgumentParser, Action

###################################################################
#
# Command Line Interface
#
###################################################################

def parser():  
  cli = ArgumentParser(prog='MyOTC',
                        description='My OTC operational calls',
                        add_help = False)
  cli.add_argument('-d','--debug', help='Enable debugging',action='store_true')
  cli.add_argument('-I','--include', help='Add Include path', action='append')
  cli.add_argument('-D','--define', help='Add constant', action='append')
  subs = cli.add_subparsers()

  deploy_cli = subs.add_parser('deploy', help='Deploy a cloud environment')
  deploy_cli.add_argument('-x','--execute', help='Execute (defaults to dry-run).  Only applies when modifying existing resources',action='store_true')
  deploy_cli.add_argument('file', help='YAML containing cloud description')
  deploy_cli.set_defaults(func = cmds.deploy_cmd)

  nuke_cli = subs.add_parser('nuke', help='Completely nuke a cloud environment')
  nuke_cli.add_argument('-x','--execute', help='Execute (defaults to dry-run)',action='store_true')
  nuke_cli.add_argument('file', help='YAML containing cloud description')
  nuke_cli.set_defaults(func = cmds.nuke_cmd)

  start_cli = subs.add_parser('start', help='Start VM')
  start_cli.add_argument('-c','--file', help='Read VMs from YAML file')
  start_cli.add_argument('name', help='VM name to start',nargs='*')
  start_cli.set_defaults(func = cmds.state_cmd, forced = False, mode = 'start')

  stop_cli = subs.add_parser('stop', help='Stop VM')
  stop_cli.add_argument('-c','--file', help='Read VMs from YAML file')
  stop_cli.add_argument('name', help='VM name to stop',nargs='*')
  stop_cli.set_defaults(func = cmds.state_cmd, forced = False, mode = 'stop')

  reboot_cli = subs.add_parser('reboot', help='Re-boot VM')
  reboot_cli.add_argument('-f','--forced', help='Hard Reboot', action='store_true')
  reboot_cli.add_argument('name', help='VM name to reboot',nargs='+')
  reboot_cli.set_defaults(func = cmds.state_cmd, forced = False, mode = 'reboot', file = None)

  vmlist_cli = subs.add_parser('vms', help='List VMs')
  vmlist_cli.add_argument('-s','--sid', help='Specify the SID to list')
  vmlist_cli.add_argument('-F','--format', help='Format to print')
  vmlist_cli.add_argument('-l','--details', help='Show detailed list',action='store_true')
  vmlist_cli.add_argument('spec', help='VM name or wildcard', nargs='*')
  vmlist_cli.set_defaults(func = shows.vmlist_cmd)

  images_cli = subs.add_parser('images', help='List images')
  images_cli.add_argument('-F','--format', help='Format to print')
  images_cli.add_argument('-l','--details', help='Show detailed list',action='store_true')
  images_cli.add_argument('spec', help='name or wildcard', nargs='*')
  images_cli.set_defaults(func = shows.imgs_cmd)

  flavors_cli = subs.add_parser('flavors', help='List flavors')
  flavors_cli.add_argument('-F','--format', help='Format to print')
  flavors_cli.add_argument('-l','--details', help='Show detailed list',action='store_true')
  flavors_cli.add_argument('--cpu',help='Specific CPU value',type=int)
  flavors_cli.add_argument('--mem',help='Specific memory value',type=int)
  flavors_cli.add_argument('--min-cpu',help='Minimum CPU value',type=int)
  flavors_cli.add_argument('--max-cpu',help='Maximum CPU value',type=int)
  flavors_cli.add_argument('--min-mem',help='Minimum memory value',type=int)
  flavors_cli.add_argument('--max-mem',help='Maximum memory value',type=int)
  flavors_cli.add_argument('spec', help='name or wildcard', nargs='*')
  flavors_cli.set_defaults(func = shows.flavors_cmd)

  vpcs_cli = subs.add_parser('vpcs', help='List VPCs')
  vpcs_cli.add_argument('-F','--format', help='Format to print')
  vpcs_cli.add_argument('-l','--details', help='Show detailed list',action='store_true')
  vpcs_cli.add_argument('spec', help='name or wildcard', nargs='*')
  vpcs_cli.set_defaults(func = shows.lists_cmd, mode='vpc',
                        format='{name:16}',
                        header='{:16}'.format('name'))

  keys_cli = subs.add_parser('keys', help='List Keys')
  keys_cli.add_argument('-F','--format', help='Format to print')
  keys_cli.add_argument('-l','--details', help='Show detailed list',action='store_true')
  keys_cli.add_argument('spec', help='name or wildcard', nargs='*')
  keys_cli.set_defaults(func = shows.lists_cmd, mode='key',
                        format='{name:16} {type:8} {short_public_key}',
                        header='{:16} {:8} {}'.format('name','type','public key'))

  nets_cli = subs.add_parser('nets', help='List nets/subnets')
  nets_cli.add_argument('-F','--format', help='Format to print')
  nets_cli.add_argument('-l','--details', help='Show detailed list',action='store_true')
  nets_cli.add_argument('spec', help='name or wildcard', nargs='*')
  nets_cli.set_defaults(func = shows.lists_cmd, mode='net',
                        format='{name:16} {cidr:16}',
                        header='{:16} {:16}'.format('name','CIDR'))

  zones_cli = subs.add_parser('dns-zones', help='List DNS zones')
  zones_cli.add_argument('-F','--format', help='Format to print')
  zones_cli.add_argument('-l','--details', help='Show detailed list',action='store_true')
  zones_cli.add_argument('spec', help='name or wildcard', nargs='*')
  zones_cli.set_defaults(func = shows.lists_cmd, mode='zone',
                        format='{name:24} {zone_type:8} {record_num:3}',
                        header='{:24} {:8} {:3}'.format('name','type','rrs'))

  sgs_cli = subs.add_parser('sgs', help='List Security Groups')
  sgs_cli.add_argument('-F','--format', help='Format to print')
  sgs_cli.add_argument('-l','--details', help='Show detailed list',action='store_true')
  sgs_cli.add_argument('spec', help='name or wildcard', nargs='*')
  sgs_cli.set_defaults(func = shows.lists_cmd, mode='sgs',
                        format='{name}',
                        header='{}'.format('name'))

  vols_cli = subs.add_parser('vols', help='List Volumes')
  vols_cli.add_argument('-F','--format', help='Format to print')
  vols_cli.add_argument('-l','--details', help='Show detailed list',action='store_true')
  vols_cli.add_argument('spec', help='name or wildcard', nargs='*')
  vols_cli.set_defaults(func = shows.lists_cmd, mode='vols',
                        format='{name:16} {size:8,} {status:12} {vm}:{vm_device}',
                        header='{:16} {:>8} {:12} {}'.format('name','size','status','vm'))

  ping_cli = subs.add_parser('ping', help='Check connectivity')
  ping_cli.add_argument('-p','--output', help='Print output',action='store_true')
  ping_cli.set_defaults(func = cmds.ping_cmd)

  parse_cli = subs.add_parser('parse', help='Parse a YAML file (syntax checking)')
  parse_cli.add_argument('-p','--preproc', help='Use pre-processor',action='store_true')
  parse_cli.add_argument('-y','--yaml', help='Parse YAML when using pre-processor',action='store_true')
  parse_cli.add_argument('file', help='YAML file to parse')
  parse_cli.set_defaults(func = ypp.yparse_cmd)

  resolv_cli = subs.add_parser('resolve', help='Resolve dependancies')
  resolv_cli.add_argument('-r','--reverse', help='Reverse dependancy list',action='store_true')
  resolv_cli.add_argument('file', help='YAML containing cloud description')
  resolv_cli.set_defaults(func = cmds.resolv_cmd)

  conout_cli = subs.add_parser('conout', help='Get console output')
  conout_cli.add_argument('-y','--yaml', help='Output YAML',action='store_true')
  conout_cli.add_argument('-l','--limit', help='Limit output to number of lines',default=50)
  conout_cli.add_argument('-L','--no-limit', help='Return all available lines', action='store_const', dest='limit', const=None)
  conout_cli.add_argument('name', help='VM name to show',nargs='+')
  conout_cli.set_defaults(func = cmds.conout_cmd)

  return cli

  
