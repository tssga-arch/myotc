#!/usr/bin/env python3
import re
from pprint import pprint

import os
import yaml

import random
import string
from passlib.hash import md5_crypt, sha256_crypt, sha512_crypt


secrets_file = '_secrets_file_'
yaml_pp_vars = dict(os.environ)
yaml_pp_vars[secrets_file] = '_secrets.yaml'
secrets = None

sshkey_re = re.compile(r'(.*)\$SSHKEY:([A-Za-z][A-Za-z0-9]*)(:[^\$]*|)\$')


for line in [
      'One two',
      'abcd $SSHKEY:linux1$',
      'abcd $$PWGEN:linux1$ something',
      'abcd $$PWGEN:linux1:32:MD5$',
      'abcd $$PWGEN:linux1:32:SHA256$  something',
      'abcd $$PWGEN:linux1:32:SHA512$',
      'abcd $PWGEN:linux1:16',
      'abcd $PWGEN:linux1 something',
      'abcd $PWGEN:linux1:32:MD5',
      'abcd $PWGEN:linux1:32:SHA256  something',
      'abcd $PWGEN:linux1:32:SHA512',
      'abcd $PWGEN:linux1:16$',
      'abcd $PWGEN:linux1$ something',
      'abcd $PWGEN:linux1:32:MD5$',
      'abcd $PWGEN:linux1:32:SHA256$  something',
      'abcd $PWGEN:linux1:32:SHA512$',
      'end' ]:

  in_line = line
  mv = pwgen_re.match(line)
  if mv:
    if mv.group(1)[-1] == '$':
      line = line[:len(mv.group(1))-1] + line[len(mv.group(1)):]
    else:
      store = mv.group(2)
      pwlen = 12
      encode = ''
      for opt in mv.group(3).split(':'):
        if not opt: continue
        if opt == 'MD5' or opt == 'SHA256' or opt == 'SHA512':
          encode = opt
        elif int(opt) > 6:
          pwlen = int(opt)

      if secrets is None:
        if os.path.isfile(yaml_pp_vars[secrets_file]):
          with open(yaml_pp_vars[secrets_file],'r') as fp:
            secrets = yaml.safe_load(fp)
        else:
          secrets = {}
      
      if store in secrets:
        passwd = secrets[store]
      else:
        charset = string.ascii_lowercase + string.ascii_uppercase + string.digits
        passwd = ''.join(random.sample(charset, pwlen))
        secrets[store] = passwd
        with open(yaml_pp_vars[secrets_file],'w') as fp:
          fp.write(yaml.dump(secrets))

      if encode == 'MD5':
        cpassw = md5_crypt.hash(passwd)
      elif encode == 'SHA256':
        cpassw = sha256_crypt.hash(passwd,rounds=5000)
      elif encode == 'SHA512':
        cpassw = sha512_crypt.hash(passwd,rounds=5000)
      else:
        cpassw = passwd

      line = line[:len(mv.group(1))]  + cpassw + line[len(mv.group(0)):]

  print('INP: {}'.format(in_line))
  print('OUT: {}'.format(line))

