# TODO

- add a way to list project resources: see
  <https://stackoverflow.com/questions/65088380/python-openstack-sdk-list-usage-for-all-projects>
  - Add flag to cli
  - If list all projects flag is true
    - Check if config has project_name already, if true, error
    - List all projects
    - Create connections with project_name set\...
    - Query servers
- myotc.exe confirm that is able to find snippets
- In show vms, handle when user doesn\'t have permission to list
  images.
- vms should be created on off state and started after all resources
  have been added/configured (i.e. attaching and resizing volumes)
- tagging
  -   default tags
  -   resource specific tags
  -   <https://github.com/opentelekomcloud/ansible-collection-cloud/blob/main/plugins/modules/tag.py>
- vpc
  - add description
  - modify subnet creation to use vpc API
    - https://docs.otc-service.com/ansible-collection-cloud/subnet_module.html
    - https://python-otcextensions.readthedocs.io/en/latest/sdk/guides/vpc.html
    - add az, dns, etc
- support for VPC peering
  - https://python-otcextensions.readthedocs.io/en/latest/sdk/guides/vpc.html
  - https://github.com/opentelekomcloud/ansible-collection-cloud/blob/main/plugins/modules/vpc_peering.py
- bandwidth pools
  - https://python-otcextensions.readthedocs.io/en/latest/sdk/guides/vpc.html
- load balancer
- Document
  - regions need to be specified in cloud.yaml
