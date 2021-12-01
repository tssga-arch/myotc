#!/usr/bin/env python3
from cfn import *
import cli
import openstack


###################################################################
#
# Main command line
#
###################################################################

if __name__ == '__main__':
  argparser = cli.parser()
  args = argparser.parse_args()
  if args.debug: openstack.enable_logging(debug=True)

  if 'func' in args:
    args.func(args)
  else:
    argparser.print_help()

  
