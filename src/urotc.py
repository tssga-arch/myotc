#!/usr/bin/env python3
''' Run only status, start, stop, reboot operations on a pre-configured VM '''
import proxycfg
import shows
import cmds
from argparse import ArgumentParser, Action
import consts as K
import os
import sys
import openstack
import os
from version import VERSION

def cliparser():
  ''' Generate CLI parser for UrOTC

  :returns: ArgumentParser
  '''
  cli = ArgumentParser(prog='UrOTC',
                        description='Your OTC operational calls',
                        add_help = False)
  cli.add_argument('-V','--version', action='version', version='%(prog)s '+VERSION)
  cli.add_argument('-d','--debug', help='Enable debugging',action='store_true')
  if proxycfg.has_winreg:
    cli.add_argument('-A','--proxy-autocfg', dest='autocfg', help='Automatically guess proxy', action='store_true')
  cli.set_defaults(cfgopts = {}, spec=[], details = False, autocfg = False)

  subs = cli.add_subparsers()
  if proxycfg.has_winreg:
    showcfg_cli = subs.add_parser('show-proxy-autocfg',help='Show proxy autocfg data')
    showcfg_cli.set_defaults(func = proxycfg.show_autocfg)

  start_cli = subs.add_parser('start', help='Start VM')
  start_cli.set_defaults(func = cmds.state_cmd, forced = False, mode = K.start)

  stop_cli = subs.add_parser('stop', help='Stop VM')
  stop_cli.set_defaults(func = cmds.state_cmd, forced = False, mode = K.stop)

  reboot_cli = subs.add_parser('reboot', help='Re-boot VM')
  reboot_cli.add_argument('-f','--forced', help='Hard Reboot', action='store_true')
  reboot_cli.set_defaults(func = cmds.state_cmd, forced = False, mode = K.reboot)

  status_cli = subs.add_parser('status', help='Show current VM state')
  status_cli.add_argument('-F','--format', help='Format to print')

  status_cli.set_defaults(func = shows.vmlist_cmd)
  return cli

def env_defaults():
  ''' Check environment to see if user has common defaults
  
  The ``sys.argv`` variable is modified accordingly
  '''
  opts = os.getenv(K.MYOTC_OPTS)
  if opts is None: return
  opts = shlex.split(opts)
  opts.reverse()
  for i in opts:
    sys.argv.insert(1,i)


def main(opts=None):
  ''' Main command entry point for UrOTC

  :param dict opts: (optional)Configuration options read from .cfg file
  '''
  cli = cliparser()
  env_defaults()
  args = cli.parse_args()
  
  if args.debug: openstack.enable_logging(debug=True)
  proxycfg.proxy_cfg(args.autocfg, args.debug)

  if 'func' in args:
    if opts:
      cf = opts
      if args.debug: sys.stderr.write('Configured from .cfg\n')
    else:
      if args.debug: sys.stderr.write('Configuring from ENV\n')
      cf = {}
      errs = []
      for k in ('TOKEN_ID','TOKEN_PSK', 'DOMAIN', 'PROJECT', 'AUTH_URL', 'RESOURCE_ID'):
        cf[k] = os.getenv(k)
        if not cf[k]: errs.append(k)

      if len(errs) > 0:
        sys.stderr.write('Missing environment variables: {vars}\n'.format( vars=str(errs) ))
        sys.exit(54)

    # ~ if has_winreg and args.autocfg:
      # ~ proxy, url, jstext = proxy_auto_cfg()
      # ~ if proxy:
        # ~ os.environ['http_proxy'] = 'http://{proxy}/'.format(proxy=proxy)
        # ~ os.environ['https_proxy'] = 'http://{proxy}/'.format(proxy=proxy)
        # ~ if args.debug:
          # ~ sys.stderr.write('Using proxy: {proxy}\n'.format(proxy=proxy))

    args.cfgopts[K.CONN] = openstack.connect(auth = {
      "username": cf['TOKEN_ID'],
      "password": cf['TOKEN_PSK'],
      "project_name": cf['PROJECT'],
      "user_domain_name": cf['DOMAIN'],
      "auth_url": cf['AUTH_URL']
    })
    args.cfgopts[K.NAME] = cf['RESOURCE_ID']
    args.func(args)
  else:
    if args.debug:
      if opts:
        sys.stderr.write('Configured from .cfg\n')
      else:
        sys.stderr.write('Configuring from ENV\n')
    cli.print_help()

if __name__ == '__main__':
  main()

