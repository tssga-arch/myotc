# MyOTC

My OTC Automation scripts

# NOTES

- [Openstack client](https://pypi.org/project/python-openstackclient/)
- [OTC extensions docs](https://python-otcextensions.readthedocs.io/en/latest/)
- [OTC extensions github](https://github.com/opentelekomcloud/python-otcextensions)

- [service proxies](https://python-otcextensions.readthedocs.io/en/latest/sdk/proxies/index.html)
- [openstack guides](https://docs.openstack.org/openstacksdk/latest/user/index.html)
- [connection object](https://docs.openstack.org/openstacksdk/latest/user/connection.html)
- [OTC Help](https://docs.otc.t-systems.com/nat/index.html)
- [block storage examples](https://docs.otc.t-systems.com/devg/sdk/sdk_02_0017.html)


- https://cloudinit.readthedocs.io/en/latest/topics/examples.html

# TODO

- how to add dns_domain?
- use resize server?
- split off myotc ->cmds.py
- re-org resource types?
- pwgen
  - $PWGEN:label:nn$
  - $PWGEN:label:MD5:nn$
  - $PWGEN:label:SHA256:nn$
  - $PWGEN:label:SHA512:nn$
  - out to stdout and/or to a file
  - save with label cleartext version, or load it if already exists
- support ssh keys
  - https://stackoverflow.com/questions/2466401/how-to-generate-ssh-key-pairs-with-python
  - cryptography module is probably included with openstacksdk
