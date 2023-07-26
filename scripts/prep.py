#
# Prepare things
#
import os
import sys
import re
from cryptography.fernet import Fernet

cfkey = Fernet.generate_key()
print(cfkey)


if len(sys.argv) != 3:
  sys.stderr.write('Usage: {cmd} src dst\n'.format(cmd=sys.argv[0]))
  sys.exit(1)

with open(sys.argv[1],'r') as inp:
  script = inp.read()

nscript = ''
found = False
for ln in script.split('\n'):
  if re.match(r'^\s*cfkey\s*=\s*',ln):
    nscript += 'cfkey  = '+str(cfkey)+'\n'
    found = True
  else:
    nscript += ln + '\n'

if not found:
  sys.stderr.write('Error finding key string cfkey assignment\n');
  sys.exit(2)

with open(sys.argv[2],'w') as outp:
  outp.write(nscript)

