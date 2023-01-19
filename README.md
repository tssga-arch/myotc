# MyOTC

My OTC Automation scripts

# Preprocessor

This software makes use of a simple pre-processor (ypp).

Command line arguments:

- -I<path> : Add <path> to the include search path
- -D<key>=<value> : Define a variable

Pre-process syntax:

- To define variables:
  - `#define key value`
- To use a variable:
  - `{key}`
  - note that it can be embedded in a string, e.g. `something {key} other`
- Escape variable:
  - `{{ ... }}`
  - Double `{{` and `}}` are replaced as single brackets.
- password generator:
  - `$PWGEN:store:len$`
    - Generate a clear text password  of `len` characters (and save
      it to the store)
  - `$PWGEN:store:MD5:len$
    - Genarate a password and encode it using UNIX MD5 hash.
  - `$PWGEN:store:SHA256:len$
  - `$PWGEN:store:SHA512:len$
    - Generate a password and encode it using SHA256 or SHA512 hashes.
  - `$PWGEN:store:vnc:len$
    - Generate a password and encode it using VNC password format.
  - `$$` PWGEN ...
    - Escape password generator
- ssh key generator:
  - `$KEYGEN:file:pub`
    - Generate public keypair and save it to `file`.  Output public key.
  - `$KEYGEN:file:priv`
    - Generate public keypair and save it to `file`.  Output private key.
  - `$$` KEYGEN
    - Escape key generator

PWGEN will save clear text version of passwords to `_secrets.yaml` or
to whatever is defined as `_secrets_file_`.

KEYGEN will save public/private key pairs as files in directory
`_keys_` or to whatever is defined as `_ssh_key_store_`.

Pre-processor conditionals:

- #ifdef <variable>
- #ifndef <variable>
- #else
- #endif

# Links

- [Openstack client](https://pypi.org/project/python-openstackclient/)
- [OTC extensions docs](https://python-otcextensions.readthedocs.io/en/latest/)
- [OTC extensions github](https://github.com/opentelekomcloud/python-otcextensions)
- [service proxies](https://python-otcextensions.readthedocs.io/en/latest/sdk/proxies/index.html)
- [openstack guides](https://docs.openstack.org/openstacksdk/latest/user/index.html)
- [connection object](https://docs.openstack.org/openstacksdk/latest/user/connection.html)
- [OTC Help](https://docs.otc.t-systems.com/nat/index.html)
- [block storage examples](https://docs.otc.t-systems.com/devg/sdk/sdk_02_0017.html)
- [OTC public services](https://imagefactory.otc.t-systems.com/home/public-services-in-otc)
- [cloud init examples](https://cloudinit.readthedocs.io/en/latest/topics/examples.html)

# Environment variables

- CLOUD : cloud to connect to (as defined by config file)
- DEFAULT_PUBLIC_DOMAIN : Domain to create public DNS records

# TODO

- change server system disk size
- use resize server?
- re-org resource types?

# Known issues

- dns-domain served by DHCP can not be configured.  This [article](https://open-telekom-cloud.com/en/support/tutorials/image-factory-image-modifications)
  suggest a solution that doesn't work.  On `ubuntu 20.04`, running the
  following command from `/etc/rc.local` seems to work:
  - `systemd-resolve --set-domain=domain --interface=ens3`

***
Use environment variable "CLOUD" to pick credentials from config files.

