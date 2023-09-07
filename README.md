# MyOTC

My OTC Automation scripts

## Preprocessor

This software makes use of a simple pre-processor (ypp).

Command line arguments:

-   -I\<path\> : Add \<path\> to the include search path
-   -D\<key\>=\<value\> : Define a variable

## Links

-   [Price
    Calculator](https://open-telekom-cloud.com/en/prices/price-calculator)
-   [Configure
    SDK](https://docs.openstack.org/openstacksdk/latest/user/config/configuration.html)
-   [Openstack client](https://pypi.org/project/python-openstackclient/)
-   [OTC extensions
    docs](https://python-otcextensions.readthedocs.io/en/latest/)
-   [OTC extensions
    github](https://github.com/opentelekomcloud/python-otcextensions)
-   [service
    proxies](https://python-otcextensions.readthedocs.io/en/latest/sdk/proxies/index.html)
-   [openstack
    guides](https://docs.openstack.org/openstacksdk/latest/user/index.html)
-   [connection
    object](https://docs.openstack.org/openstacksdk/latest/user/connection.html)
-   [OTC Help](https://docs.otc.t-systems.com/nat/index.html)
-   [block storage
    examples](https://docs.otc.t-systems.com/devg/sdk/sdk_02_0017.html)
-   [OTC public
    services](https://imagefactory.otc.t-systems.com/home/public-services-in-otc)
-   [cloud init
    examples](https://cloudinit.readthedocs.io/en/latest/topics/examples.html)

## Environment variables

Configuration can be done by defining the following environment
variables:

-   `CLOUD` : cloud to connect to (as defined by config file), defaults
    to `otc`.
-   `PROJECT` : If config file does not specify project, this can be
    used to override the default project name.
-   `SID` : SID for environment
-   `PUBLIC_DNS_ZONE` : Public DNS domain in OTC to update
-   `PRIVATE_DNS_ZONE` : Private DNS domain to create for this SID
    (defaults to `nova.`)
-   `DEFAULT_IMAGE` : Default image to use (if not specified)
-   `DEFAULT_FLAVOR` : Default VM flavor to use (if not specified)
-   `MYOTC_OPTS` : Additional config variables
-   `CIDR_BLOCK` : CIDR block to use for the VPC (needed for peering).
    Otherwise defaults to 10.0.0.0/16

Additionally, these can be defined in the commandline with
[-Dxxx=yyyy]{.title-ref} or in the YAML file with [#define xxx
yyy]{.title-ref} statements

## Known issues

-   dns-domain served by DHCP can not be configured. This
    [article](https://open-telekom-cloud.com/en/support/tutorials/image-factory-image-modifications)
    suggest a solution that doesn\'t work. On `ubuntu 20.04`, running
    the following command from `/etc/rc.local` seems to work:
    -   `systemd-resolve --set-domain=domain --interface=ens3`
-   Only VMs are tagged with SID={sid}
    -   See
        [ansible-tags-module](https://github.com/opentelekomcloud/ansible-collection-cloud/blob/6b1d83c0bd24318ceda0d6395c3fe4f05cb2375c/plugins/modules/tag.py)
    -   testing on network resources yield errors. Don\'t know if
        volumes can be tagged.
    -   Sample code:

``` python
c = cf[CLOUD]
vm = c.compute.find_server('simp1-vm1')
if 'name' in vm:
 print(vm.name)
 # vm.add_tag(c.compute, 'PROJECT=kermit')
 i = vm.fetch_tags(c.compute)
 pprint(i.tags)
```
