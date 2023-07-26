#
# Example PRIV
#
import os
import sys
from cryptography.fernet import Fernet
import urotc

cfkey = Fernet.generate_key()

f = Fernet(cfkey)
def readcfg():
  cfgfile = cfname()
  opts = dict()
  with open(cfgfile,'rb') as fp:
    cfencr = fp.read()
    cfblob = f.decrypt(cfencr)

    for ln in cfblob.decode().split('\n'):
      ln = ln.strip()
      if  not ':' in ln: continue
      k = ln.split(':',1)
      opts[k[0]] =  k[1]

  return opts

def cfname():
  if getattr(sys,'frozen',False):
    run = sys.executable
  else:
    run = __file__
  run = os.path.abspath(run)
  dirname = os.path.dirname(run)
  basename = os.path.basename(run)
  # ~ print('dirname={dirname}'.format(dirname=dirname))
  # ~ print('basename={basename}'.format(basename=basename))

  if '.' in basename:
    # Remove file extension
    i = basename.find('.')
    if i > 0: basename = basename[:i]

  return dirname + os.path.sep + basename + '.cfg'


if len(sys.argv) >= 2 and sys.argv[1] == 'encode':
  # encode config
  cfgfile = cfname()

  # Read current config
  try:
    incf = readcfg()
  except:
    sys.stderr.write('{cfgfile}: Read Error.  Creating it...\n'.format(cfgfile=cfgfile))
    incf = {}

  interactive = False
  kn = ('TOKEN_ID','TOKEN_PSK', 'DOMAIN', 'PROJECT', 'AUTH_URL', 'RESOURCE_ID')
  print('keys: {}'.format(str(kn)))

  # Read from environment
  for k in kn:
    cf = os.getenv(k)
    if cf is None: continue
    incf[k] = cf

  # Check command line
  for kv in sys.argv[2:]:
    if kv == '-i':
      interactive = True
      continue
    elif '=' in kv:
      i = kv.index('=')
      k = kv[:i]
      v = kv[i+1:]
    else:
      k = kv
      v = kv
    k = k.lstrip('-').upper().translate(str.maketrans({'-':'_'}))
    if not k in kn:
      sys.stderr.write('{}: Unrecognized option\n'.format(kv))
      continue
    incf[k] = v

  # Check if keys are there, otherwise ask for them
  for k in kn:
    if k in incf and incf[k] != '':
      if not interactive: continue
    else:
      incf[k] = ''
      sys.stderr.write('{k}: missing key\n'.format(k=k))
    v = input('Enter {key}: ({value}) '.format(key=k,value=incf[k]))
    if v != '': incf[k] = v

  # Create config block
  cfblob = ''
  for k in incf:
    cfblob += k +':'+incf[k] +'\n'
  print(cfblob)

  # Encrypt and save
  cfencr = f.encrypt(cfblob.encode())
  print('Writing to {cfgfile}'.format(cfgfile=cfgfile))
  with open(cfgfile,'wb') as fp:
    fp.write(cfencr)

  sys.exit(0)


#
# Actual run...
#
urotc.main(readcfg())

