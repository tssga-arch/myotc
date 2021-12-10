#!/usr/bin/env python3
import base64
import yaml
import sys
import re
import os
import random
import string
from passlib.hash import md5_crypt, sha256_crypt, sha512_crypt
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

###################################################################
#
# YAML related utilities
#
###################################################################
yaml_include_path = []
secrets_file = '_secrets_file_'
key_store = '_ssh_key_store_'
yaml_pp_vars = dict(os.environ)

valid_re = re.compile(r'^[A-Za-z][A-Za-z0-9]*$')

def yaml_init(inc_path, predef):
  if not secrets_file in yaml_pp_vars:
    yaml_pp_vars[secrets_file] = '_secrets.yaml'
  if not key_store in yaml_pp_vars:
    yaml_pp_vars[key_store] = '_keys_'

  if inc_path:
    for inc in inc_path:
      if os.path.isdir(inc):
        yaml_include_path.append(inc)
  if predef:
    for kvp in predef:
      if '=' in kvp:
        kvp = kvp.split('=',1)
        key = kvp[0]
        val = kvp[1]
      else:
        key = kvp
        val = ''
      if valid_re.match(key):
        yaml_pp_vars[key] = val
      else:
        print('{} is not a valid name'.format(key))

def yaml_findfile(fname, prev):
  if fname[0] == '/':
    # This is an absolute path!
    return fname

  if prev:
    dn = os.path.dirname(prev)
    if dn == '':
      tname = fname
    else:
      tname = '{}/{}'.format(dn,fname)
    if os.path.isfile(tname): return tname

  for dn in yaml_include_path:
    tname = '{}/{}'.format(dn,fname)
    if os.path.isfile(tname): return tname

  # Otherwise just hope for the best!
  return fname

include_res = [ re.compile(r'^(\s*)#\s*include\s+') , re.compile(r'^(\s*-\s*)#\s*include\s+')]
include_type = re.compile(r'\s*--(raw|bin)\s+')

def yaml_inc(line):
  for inc_re in include_res:
    mv = inc_re.match(line)
    if mv is None: continue

    fname = line[mv.end():]
    prefix = mv.group(1)

    mv = include_type.match(fname)
    if mv:
      fname = fname[mv.end():]
      inctype = mv.group(1)
    else:
      inctype = None
    return { 'file': fname, 'prefix': prefix, 'type': inctype }
  return None

def yaml_raw(fname, prefix = '', prev = None):
  txt = ''
  prefix2 = prefix.replace('-',' ')
  fname = yaml_findfile(fname, prev)

  with open(fname,'r') as f:
    for line in f:
      if line.endswith("\n"): line = line[:-1]
      if line.endswith("\r"): line = line[:-1]
      txt += prefix + line + "\n"
      prefix = prefix2

  return txt

def yaml_bin(fname, prefix = '', prev = None):
  txt = ''
  prefix2 = prefix.replace('-',' ')
  fname = yaml_findfile(fname, prev)

  with open(fname,'rb') as f:
    b64 = base64.b64encode(f.read()).decode('ascii')
    i = 0
    while i < len(b64):
      txt += prefix + b64[i:i+76] + "\n"
      prefix = prefix2
      i += 76

  return txt

keygen_re = re.compile(r'(.*)\$KEYGEN:([A-Za-z][A-Za-z0-9]*)(:[^\$]*|)\$')
def sshkeygen(line):
  mv = keygen_re.match(line)
  if not mv: return line

  if mv.group(1)[-1] == '$':
    return line[:len(mv.group(1))-1] + line[len(mv.group(1)):]

  store = mv.group(2)
  mode = 'pub'
  key_sz = 2048

  for opt in mv.group(3).split(':'):
    if not opt: continue
    if opt == 'pub' or opt == 'priv':
      mode = opt
      continue
    elif opt.isnumeric():
      key_sz = int(opt)

  keydir= yaml_pp_vars[key_store]
  if not os.path.isdir(keydir): os.mkdir(keydir)
  if os.path.isfile(keydir + "/" + store) and os.path.isfile(keydir + '/' + store + '.pub'):
    with open(keydir + "/" + store,'r') as fp:
      private_key = fp.read().strip()
    with open(keydir + "/" + store + '.pub','r') as fp:
      public_key = fp.read().strip()
  else:
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=key_sz
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption()
    ).decode('ascii')
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    ).decode('ascii')
    with open(keydir + "/" + store,'w') as fp:
      fp.write(private_key + "\n")
    with open(keydir + "/" + store + '.pub','w') as fp:
      fp.write(public_key + "\n")

  if mode == 'pub':
    okey = public_key
  else:
    okey = private_key

  lines = []

  for part in okey.split("\n"):
    lines.append(line[:len(mv.group(1))]  + part + line[len(mv.group(0)):])

  return "\n".join(lines)

pwgen_re = re.compile(r'(.*)\$PWGEN:([A-Za-z][A-Za-z0-9]*)(:[^\$]*|)\$')

def pwgen(line):
  secrets = None
  mv = pwgen_re.match(line)
  if not mv: return line

  if mv.group(1)[-1] == '$':
    return line[:len(mv.group(1))-1] + line[len(mv.group(1)):]

  store = mv.group(2)
  pwlen = 12
  encode = ''
  for opt in mv.group(3).split(':'):
    if not opt: continue
    if opt == 'MD5' or opt == 'SHA256' or opt == 'SHA512':
      encode = opt
    elif opt.isnumeric():
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
    print('Generated password for {store} as {passwd}'.format(store=store,passwd=passwd))

  if encode == 'MD5':
    cpassw = md5_crypt.hash(passwd)
  elif encode == 'SHA256':
    cpassw = sha256_crypt.hash(passwd,rounds=5000)
  elif encode == 'SHA512':
    cpassw = sha512_crypt.hash(passwd,rounds=5000)
  else:
    cpassw = passwd

  return line[:len(mv.group(1))]  + cpassw + line[len(mv.group(0)):]

define_re = re.compile(r'^\s*#\s*define\s+([A-Za-z][A-Za-z0-9]*)\s*')

def yaml_pp(fname, prefix = '', prev = None):
  txt = ''
  prefix2 = prefix.replace('-',' ')

  fname = yaml_findfile(fname, prev)

  with open(fname,'r') as f:
    for line in f:
      if line.endswith("\n"): line = line[:-1]
      if line.endswith("\r"): line = line[:-1]
      mv = define_re.match(line)
      if mv:
        yaml_pp_vars[mv.group(1)] = line[mv.end():].format(**yaml_pp_vars)
        continue

      mv = yaml_inc(line)
      if mv:
        if mv['type'] == 'raw':
          txt += yaml_raw(mv['file'], prefix = prefix2+mv['prefix'], prev=fname)
        elif mv['type'] == 'bin':
          txt += yaml_bin(mv['file'], prefix = prefix2+mv['prefix'], prev=fname)
        else:
          txt += yaml_pp(mv['file'], prefix = prefix2+mv['prefix'], prev=fname)
        continue

      line = prefix + line.format(**yaml_pp_vars)

      txt += sshkeygen(pwgen(line)) + "\n"
      prefix = prefix2

  return txt

def yparse_cmd(args):
  if args.yaml:
    if args.preproc:
      yaml_init(args.include, args.define)
      ytxt = yaml_pp(args.file)
    else:
      ytxt = open(args.file, 'r')
    res = yaml.safe_load(ytxt)
    print(res)
  else:
    yaml_init(args.include, args.define)
    txt = yaml_pp(args.file)
    print(txt)

def dump(data):
  return yaml.dump(data)

def process(yamlfile, includes, defines):
  yaml_init(includes, defines)
  return yaml.safe_load(yaml_pp(yamlfile))

def load(thing):
  return yaml.safe_load(thing)

###################################################################
#
# Main command line
#
###################################################################

if __name__ == '__main__':
  from argparse import ArgumentParser, Action

  cli = ArgumentParser(prog='ypp',description='YAML file pre-processor')
  cli.add_argument('-I','--include', help='Add Include path', action='append')
  cli.add_argument('-D','--define', help='Add constant', action='append')

  cli.add_argument('-y','--yaml', help='Parse YAML',action='store_true')
  cli.add_argument('-p','--preproc', help='Use pre-processor when parsing yaml',action='store_true')
  cli.add_argument('file', help='YAML file to parse')

  args = cli.parse_args()
  yparse_cmd(args)
  sys.exit()
