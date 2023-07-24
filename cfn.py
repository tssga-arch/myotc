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

DEFAULT_TAGS = 10

cf = [
  None, None, None, None,
  'Standard_CentOS_8_latest', 's3.medium.2',
  [ '100.125.4.25', '100.125.129.199' ],
  os.getenv('DEFAULT_PUBLIC_DOMAIN','otc1.cloudkit7.xyz.'),
  'nova.', '10.{id_hi}.{id_lo}.0/24',
  None,
]
if not cf[DEFAULT_PUBLIC_DNS_ZONE].endswith('.'):
  cf[DEFAULT_PUBLIC_DNS_ZONE] += '.'

def pprint(z):
  cf[CLOUD].pprint(z)

def my_otc(sid = None):
  # ~ print(sys.env["HOME"])
  auth = os.getenv('CLOUD','otc')
  cf[CLOUD] = openstack.connect(cloud=auth)
  cf[SID] = sid
  return cf[CLOUD]


#
# Support functions
#


