import openstack

c = openstack.connect(cloud='otc')

vpc = c.vpc.vpcs()

for v in vpc:
  print(v)
  print('-')
