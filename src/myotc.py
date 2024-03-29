#!/usr/bin/env python3
###################################################################
'''Main command line'''
###################################################################
import cli
import openstack
import os
import ypp
import sys
from dataclasses import dataclass
import consts as K
import shlex
import proxycfg

@dataclass
class Settings:
  ''' Data structure containing MyOTC settings '''
  connection: openstack.connection
  ''' Currently active OpenStack connection '''

settings = Settings(
  None,
)
DEFAULT_NAME_SERVERS = [ '100.125.4.25', '100.125.129.199' ]


def msg(text):
  '''Output message to stderr with autoflush

  :param str text: text to display
  '''
  sys.stderr.write(text)
  sys.stderr.flush()


def gen_name(id_or_name, prefix, sid):
  '''Generate resource name

  :param int|str id_or_name: ID or Name of resource
  :param str prefix: prefix identifying the resource type
  :param str sid: system ID
  :returns str: generate name
  '''
  if isinstance(id_or_name,int):
    return '{sid}-{prefix}{id}'.format(sid=sid,prefix=prefix,id=id_or_name)
  name = str(id_or_name)
  if name.startswith(sid+'-'):
    return name
  return '{}-{}'.format(sid,name)

def connect(args = None):
  ''' Create an OpenStack connection object

  :param namespace args: namespace generated by a CLI parser
  :returns openstack.connection: OpenStack connection
  '''
  project = None
  if settings.connection is None:
    if not args is None and 'include' in args and 'define' in args:
      if 'file' in args and not args.file is None:
        ypp.process(args.file, args.include, args.define)
      else:
        ypp.yaml_init(args.include, args.define)
      auth = ypp.vars(K.CLOUD, K.DEFAULT_CLOUD)
      project = ypp.vars(K.PROJECT, None)
    else:
      auth = os.getenv(K.CLOUD, K.DEFAULT_CLOUD)
      project = os.getenv(K.PROJECT, None)

    cloud = { 'cloud': auth }
    cloud_region = openstack.config.get_cloud_region(**cloud)    
    if not 'project_name' in cloud_region.config['auth']:
      # No project_name defined!
      if project is None:
        project = cloud_region.config['region_name']
        sys.stderr.write('Assuming "{region}" for project name\n'.format(region=project))
      cloud['project_name'] = project

    settings.connection = openstack.connect(**cloud)
  return settings.connection

def sanitize_dns_name(zname):
  return zname.rstrip('.')+'.'

def pprint(dat):
  ''' ``pprint`` for OpenStack objects

  :param mixed dat: OpenStack object to pretty print.
  '''
  settings.connection.pprint(dat)

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

if __name__ == '__main__':
  argparser = cli.parser()
  env_defaults()
  args = argparser.parse_args()
  if args.debug: openstack.enable_logging(debug=True)
  proxycfg.proxy_cfg(args.autocfg, args.debug)

  if 'func' in args:
    args.func(args)
  else:
    argparser.print_help()


