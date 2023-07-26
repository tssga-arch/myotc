#
# Get version as defined by GIT
#
import subprocess
import sys

cwd = '.'
rc = subprocess.run(['git','describe'],
                      capture_output=True,
                      text=True,
                      cwd=cwd)
if rc.returncode == 0:
  outp = 'VERSION = \'{}\'\n'.format(rc.stdout.strip())
  if len(sys.argv) == 2:
    with open(sys.argv[1],'w') as fp:
      fp.write(outp)
  else:
    print(outp)
else:
  sys.stderr.write('RUN ERROR: {}\n'.format(str(rc)))
  sys.exit(1)

  
