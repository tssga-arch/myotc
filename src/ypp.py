#!/usr/bin/env python3
''' YAML pre-processor module

This can be used as python module or as a command line.

If used on the command line, it acts as a pre-processor reading
YAML files with pre-processor directives, and outputs
the processed file.

Optionally it can parse the generated YAML and dump it as a JSON
object (which is also valid YAML document)
'''
import base64
import yaml
import sys
import re
import os
import random
import string
import subprocess
import json
from d3des import encrypt as d3des
from argparse import ArgumentParser, Action
from version import VERSION

try:
  from passlib.hash import md5_crypt, sha256_crypt, sha512_crypt
  from cryptography.hazmat.primitives import serialization as crypto_serialization
  from cryptography.hazmat.primitives.asymmetric import rsa
  from cryptography.hazmat.backends import default_backend as crypto_default_backend
except ImportError:
  pass

###################################################################
#
# YAML related utilities
#
###################################################################
yaml_include_path = []
''' List of folders where to find included files '''
secrets_file = '_secrets_file_'
''' variable name for secrets file in the yaml_pp_vars dictionary '''
key_store = '_ssh_key_store_'
''' variable name for the keystore folder in the yaml_pp_vars dictionary '''

yaml_pp_vars = dict(os.environ)
''' dictonary containing pre-processor variable definitions '''
if 'sphinx' in sys.modules:
  yaml_pp_vars = { 'content_of': 'os environment' }

valid_re = re.compile(r'^[_A-Za-z][_A-Za-z0-9]*$')
''' Regular expressions to validate pre-processor variable names '''

def vars(value, default = None):
  ''' Look-up pre-processor values

  :param str value: variable to look-up
  :param str default: (optional) value to return if variable does not exist
  :returns None|str: defined variable
  '''
  if value in yaml_pp_vars:
    return yaml_pp_vars[value]
  return default

def yaml_init(inc_path, predef):
  ''' Initialize YAML pre-processor

  :param list inc_path: list of folders to initialize include path
  :param list predef: list of strings formatted as key=value pairs to initialize the YAML pre-processor variables

  This function is intended to be used to initialie the pre-processor
  internal variables from arguments entered in the command line.

  '''
  if not secrets_file in yaml_pp_vars:
    if os.path.isfile('_secrets.yaml'):
      yaml_pp_vars[secrets_file] = '_secrets.yaml'
    elif os.path.isfile('../secrets/_secrets.yaml'):
      yaml_pp_vars[secrets_file] = '../secrets/_secrets.yaml'
    else:
      yaml_pp_vars[secrets_file] = '_secrets.yaml'
  if not key_store in yaml_pp_vars:
    if os.path.isdir('_keys_'):
      yaml_pp_vars[key_store] = '_keys_'
    elif os.path.isdir('../secrets'):
      yaml_pp_vars[key_store] = '../secrets'
    else:
      yaml_pp_vars[key_store] = '_keys_'
  # ~ print("secrets_file: "+yaml_pp_vars[secrets_file])
  # ~ print("key_store: " + yaml_pp_vars[key_store])

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
  ''' Find included file path

  :param str fname: Filename to include
  :param str prev: Current file name being processed
  :returns str: Resolved included file

  First it tries to file as a relative to the current (prev) file.
  If not found, search for it in the Include path.
  '''
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
''' Regular expressions to search for include files '''
include_type = re.compile(r'\s*--(raw|bin)\s+')
''' Regular expression to determine the include type '''

def yaml_inc(line):
  ''' Process include statement

  :param str line: Line that potentially contains the include statement
  :returns None|dict: Returns None if not a include statement, if include statement, a dict.

  Look into the read line and check if it is an "include" statement.
  When found, it returns a dictionary containing:

  * file : Included file
  * prefix : Whitespace in front of the include statement.  Used to nest YAML structures.
  * type : type of include, "raw", "bin" or None.

  If the line did not contain an include statement, returns None.
  '''
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
  ''' Include file verbatim

  :param str fname: File to include
  :param str prefix: (optional) lines are prepended with ``prefix``
  :param str prev: (optional) Not used, but kept to maintain interface

  Includes a file without doing any pre-processing.  No variable
  expansion nor include statements.

  Prefix is still used.  This is to maintiain the YAML file structure.
  '''
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
  ''' Include binary file

  :param str fname: File to include
  :param str prefix: (optional) lines are prepended with ``prefix``
  :param str prev: (optional) Not used, but kept to maintain interface

  Include binary file as MIME/Base64 encoded text.

  Prefix is used to maintain YAML file structure.
  '''

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
''' Regular expression to detect sshkey macros '''

def sshkeygen(line):
  ''' Process SSH Keygen lines

  :param str line: line being processed
  :returns str: Post-processed line

  Looks for KEYGEN macros and replaces them with SSH Private or Public
  keys.  It will either read them from the ``key_store`` or will
  create a new key as needed.
  '''
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

pwgen_re = re.compile(r'(.*)\$PWGEN:([_A-Za-z][_A-Za-z0-9]*)(:[^\$]*|)\$')
''' regular expression to parse PWGEN macros '''

def pwgen(line):
  ''' Handle PWGEN macros

  :param str line: line being processed
  :returns str: Post-processed line

  Looks for PWGEN macros and replaces them with the specified password.
  It will either read them from the ``secrets_file`` or will
  create a new password as needed.

  Post-processed line will contain the specified password and this can
  be formatted according to the macro's arguments.
  '''

  secrets = None
  mv = pwgen_re.match(line)
  while mv:
    if mv.group(1)[-1] == '$':
      return line[:len(mv.group(1))-1] + line[len(mv.group(1)):]

    store = mv.group(2)
    pwlen = 12
    encode = ''
    for opt in mv.group(3).split(':'):
      if not opt: continue
      if opt == 'MD5' or opt == 'SHA256' or opt == 'SHA512' or opt == 'vnc':
        encode = opt
      elif opt.isnumeric():
        pwlen = int(opt)

    if secrets is None:
      if os.path.isfile(yaml_pp_vars[secrets_file]):
        with open(yaml_pp_vars[secrets_file],'r') as fp:
          secrets = yaml.safe_load(fp)
        if not secrets: secrets = {} # Handle empty files
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
    elif encode == 'vnc':
      cpassw = d3des(passwd)
    else:
      cpassw = passwd

    line = line[:len(mv.group(1))]  + cpassw + line[len(mv.group(0)):]
    mv = pwgen_re.match(line)
  return line

define_re = re.compile(r'^\s*#\s*define\s+([_A-Za-z][_A-Za-z0-9]*)\s*')
''' Regular expression to parse define statements '''
default_re = re.compile(r'^\s*#\s*default\s+([_A-Za-z][_A-Za-z0-9]*)\s*')
''' Regular expression to parse default statements '''
ifdef_re = re.compile(r'^\s*#\s*ifdef\s+([_A-Za-z][_A-Za-z0-9]*)\s*')
''' Regular expression to parse ifdef statements '''
ifndef_re = re.compile(r'^\s*#\s*ifndef\s+([_A-Za-z][_A-Za-z0-9]*)\s*')
''' Regular expression to parse ifndef statements '''
else_re = re.compile(r'^\s*#\s*else\s*')
''' Regular expression to parse else statements '''
endif_re = re.compile(r'^\s*#\s*endif\s*')
''' Regular expression to parse endif statements '''
exec_re = re.compile(r'^(\s*)#\s*exec\s+(.*)$')
''' Regular expression to parse exec statements '''
error_re = re.compile(r'^(\s*)#\s*error\s+(.*)$')
''' Regular expression to parse error statements '''
warn_re = re.compile(r'^(\s*)#\s*warn\s+(.*)$')
''' Regular expression to parse warn statements '''


def yaml_pp(fname, prefix = '', prev = None):
  ''' Pre-process the given file name

  :param str fname: File name to pre-process
  :param str prefix: (optional) Prefix string to maintain YAML structure
  :param str prev: (optional) Previously processed file that is including this file.
  :returns str: post-processed file contents

  This is the main YAML pre-processor functions.  Implements most of the
  logic related to YAML pre-processing.

  It takes a file as input, executes the pre-processing statements
  and returns the results as a text string.
  '''
  txt = ''
  prefix2 = prefix.replace('-',' ')
  cond_stack = []

  fname = yaml_findfile(fname, prev)

  with open(fname,'r') as f:
    for line in f:
      if line.endswith("\n"): line = line[:-1]
      if line.endswith("\r"): line = line[:-1]
      if len(cond_stack):
        # In Conditional
        mv = else_re.match(line)
        if mv:
          # It is an else match...
          cond_stack[0] = not cond_stack[0]
          continue
        mv = endif_re.match(line)
        if mv:
          # It is an endif match... so pop the stack!
          cond_stack = cond_stack[1:]
          continue
        if not cond_stack[0]:
          # supressing output...
          mv = ifdef_re.match(line)
          if mv:
            # handle a nested ifdef
            cond_stack.insert(0,False)
            continue
          mv = ifndef_re.match(line)
          if mv:
            # handle a nested ifndef
            cond_stack.insert(0,False)
            continue
          continue

      mv = ifdef_re.match(line)
      if mv:
        if mv.group(1) in yaml_pp_vars:
          cond_stack.insert(0,True)
        else:
          cond_stack.insert(0,False)
        continue
      mv = ifndef_re.match(line)
      if mv:
        if mv.group(1) in yaml_pp_vars:
          cond_stack.insert(0,False)
        else:
          cond_stack.insert(0,True)
        continue

      mv = define_re.match(line)
      if mv:
        yaml_pp_vars[mv.group(1)] = line[mv.end():].format(**yaml_pp_vars)
        continue

      mv = default_re.match(line)
      if mv:
        if not mv.group(1) in yaml_pp_vars:
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

      mv = exec_re.match(line)
      if mv:
        cwd = os.path.dirname(fname)
        if cwd == '': cwd=None
        rc = subprocess.run(mv.group(2),
                            capture_output=True,
                            shell=True,
                            text=True,
                            cwd=cwd)
        if rc.returncode != 0:
          sys.stderr.write('Command: {cmd} exited status {st}\n'.format(
                            cmd=mv.group(1),
                            st=rc.returncode))
        if rc.stderr != '': sys.stderr.write(rc.stderr)
        for i in rc.stdout.split('\n'):
          txt += prefix + mv.group(1) + i +'\n'

        continue

      mv = error_re.match(line)
      if mv:
        sys.stderr.write(mv.group(2) + '\n')
        sys.exit(1)
      mv = warn_re.match(line)
      if mv:
        sys.stderr.write(mv.group(2) + '\n')
        continue

      line = prefix + line.format(**yaml_pp_vars)

      txt += sshkeygen(pwgen(line)) + "\n"
      prefix = prefix2

  return txt

def cmd_cli():
  ''' Command Line Interface argument parser '''
  cli = ArgumentParser(prog='ypp',description='YAML file pre-processor')
  cli.add_argument('-I','--include', help='Add Include path', action='append')
  cli.add_argument('-D','--define', help='Add constant', action='append')
  cli.add_argument('-V','--version', action='version', version='%(prog)s '+VERSION)

  cli.add_argument('-y','--yaml', help='Parse YAML',action='store_true')
  cli.add_argument('-p','--preproc', help='Use pre-processor when parsing yaml',action='store_true')
  cli.add_argument('file', help='YAML file to parse')
  return cli

def yparse_cmd(args):
  '''  ypp main function

  :param Namespace args: namespace contains passed CLI passed options

  Main entry point for ypp command
  '''
  if args.yaml:
    if args.preproc:
      yaml_init(args.include, args.define)
      ytxt = yaml_pp(args.file)
    else:
      ytxt = open(args.file, 'r')
    res = yaml.safe_load(ytxt)
    print(json.dumps(res))
  else:
    yaml_init(args.include, args.define)
    txt = yaml_pp(args.file)
    print(txt)

def dump(data):
  ''' Alias for ``yaml.dump``

  :param mixed data: data to dump.
  :returns str: YAML dump of data
  '''
  return yaml.dump(data)

def process(yamlfile, includes, defines):
  ''' Main entry point for YPP embedding

  :param str yamlfile: File to process
  :param list includes: List containing include directories
  :param list defines: List containing strings to define.
  :returns data: post-processed and YAML parsed data.

  Reads the input yamlfile, and pre-processed.  The caller can specified
  a list of directories (as specfied by the list ``includes`` to use for
  the include path.  Also, the ``defines`` list can be used to initialize
  the pre-processor variables.

  '''

  yaml_init(includes, defines)
  return yaml.safe_load(yaml_pp(yamlfile))

def load(thing):
  ''' Alias for ``yaml.safe_load``

  :param str thing: input for ``safe_load``
  :returns mixed: data read from YAML entity
  '''
  return yaml.safe_load(thing)

###################################################################
#
# Main command line
#
###################################################################

if __name__ == '__main__':
  cli = cmd_cli()
  args = cli.parse_args()
  yparse_cmd(args)
  sys.exit()
