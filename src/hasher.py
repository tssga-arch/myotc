#!/usr/bin/env python3
''' Simple utility to generate hashed passwords '''
from d3des import encrypt as d3des
from argparse import ArgumentParser, Action
try:
  from passlib.hash import md5_crypt, sha256_crypt, sha512_crypt
except ImportError:
  pass
from version import VERSION

def passwdcalc_cli():
  '''passwdcat utility CLI generator'''
  cli = ArgumentParser(prog='hasher',description='Calculate hashes of password strings')
  cli.add_argument('-V','--version', action='version', version='%(prog)s '+VERSION)
  cli.add_argument('-1', '--md5', action = 'store_const', const ='MD5', dest = 'encode',
                    help = 'Encode md5 password')
  cli.add_argument('-5', '--sha256', action = 'store_const', const ='SHA256', dest = 'encode',
                    help = 'Encode SHA256 password')
  cli.add_argument('-6', '--sha512', action = 'store_const', const ='SHA512', dest = 'encode',
                    help = 'Encode SHA512 password')
  cli.add_argument('--vnc', action = 'store_const', const ='vnc', dest = 'encode',
                    help = 'Encode VNC password')
  cli.add_argument('passwd', help='Password to encode')
  cli.set_defaults(encode = 'MD5')
  return cli

if __name__ == '__main__':
  cli = passwdcalc_cli()
  args = cli.parse_args()

  if args.encode == 'MD5':
    cpassw = md5_crypt.hash(args.passwd)
  elif args.encode == 'SHA256':
    cpassw = sha256_crypt.hash(args.passwd,rounds=5000)
  elif args.encode == 'SHA512':
    cpassw = sha512_crypt.hash(args.passwd,rounds=5000)
  elif args.encode == 'vnc':
    cpassw = d3des(args.passwd)

  print(cpassw)
