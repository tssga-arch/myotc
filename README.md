# MyOTC

My OTC automation scripts

# NOTES

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

# TODO

- use resize server?
- re-org resource types?
- pwgen
  - $PWGEN:label:nn$
  - $PWGEN:label:MD5:nn$
  - $PWGEN:label:SHA256:nn$
  - $PWGEN:label:PWSHA512:nn$
  - out to stdout and/or to a file
  - save with label cleartext version
  - https://serverfault.com/questions/330069/how-to-create-an-sha-512-hashed-password-for-shadow
  - https://medium.com/analytics-vidhya/create-a-random-password-generator-using-python-2fea485e9da9
  - https://stackoverflow.com/questions/2466401/how-to-generate-ssh-key-pairs-with-python

# Known issues

- dns-domain served by DHCP can not be configured.  This [article](https://open-telekom-cloud.com/en/support/tutorials/image-factory-image-modifications)
  suggest a solution that doesn't work.  On `ubuntu 20.04`, running the
  following command from `/etc/rc.local` seems to work:
  - `systemd-resolve --set-domain=domain --interface=ens3`

