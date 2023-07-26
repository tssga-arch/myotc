#
# Get version as defined by GIT
#
import subprocess
import sys
import os

version = os.getenv('GITHUB_REF_NAME')
if version is None:
  cwd = '.'
  rc = subprocess.run(['git','describe'],
                      capture_output=True,
                      text=True,
                      cwd=cwd)
  if rc.returncode != 0:
    sys.stderr.write('RUN ERROR: {}\n'.format(str(rc)))
    sys.exit(1)
  version = rc.stdout.strip()


outp = 'VERSION = \'{}\'\n'.format(version)
if len(sys.argv) == 2:
  with open(sys.argv[1],'w') as fp:
    fp.write(outp)
else:
  print(outp)
