# https://docs.openstack.org/openstacksdk/latest/user/guides/connect.html
# https://platform9.com/docs/openstack/cli-access-multi-cloud-cli#using-os-client-config-from-the-api
import openstack
import keystoneauth1

# ~ os = openstack.connect(cloud='otc' , region_name = 'eu-nl', project_name = 'eu-nl') # NO
# ~ os = openstack.connect(cloud='otc' , project_name = 'eu-de_shared1') # NO
# ~ os = openstack.connect(cloud='otc' , region_name = 'eu-nl') # NO


#  otc-none:
#    profile: otc
#    auth: ...
#    regions:
#    - eu-nl
#    - eu-de

# ~ os = openstack.connect(cloud='otc-none') # NO
# ~ os = openstack.connect(cloud='otc-none', project_name = 'eu-de_shared1', region_name='eu-de') # YES
# ~ os = openstack.connect(cloud='otc-none', project_name = 'eu-de', region_name='eu-de') # YES
# ~ os = openstack.connect(cloud='otc-none', project_name = 'eu-nl') # NO
# ~ os = openstack.connect(cloud='otc-none', project_name = 'eu-nl', region_name='eu-nl') # YES
# ~ os = openstack.connect(cloud='otc-none', region_name = 'eu-nl') # NO

#  otc-de:
#    profile: otc
#    auth: ...
#    regions_name: eu-de
# ~ os = openstack.connect(cloud='otc-de') # NO
# ~ os = openstack.connect(cloud='otc-de', project_name='eu-de') # YES

# clouds.yaml 
#   Entry must specify region
#   Project_Name is optional, if unspecified, defaults to region_name
#   If specified then user can not specify project_name as a -D
#   -DPROJECT can be spcified if clouds.yaml entry does not provide one

# 

# OPTION-1
# ~ cloud = { 'cloud': 'otc-de' }
# ~ cloud = { 'cloud': 'otc-de-shared1' }
# ~ cloud = { 'cloud': 'otc' }
cloud = { 'cloud': 'otc', 'project_name': 'otc-de-shared1' }
# ~ cloud = { 'cloud': 'otc-test' }
# ~ cloud = { 'cloud': 'otc-nl' }
# ~ cloud = { 'cloud': 'otc-none' }

cloud_region = openstack.config.get_cloud_region(**cloud)
if not 'project_name' in cloud_region.config['auth']:
  # Check if user defines it...
  print('Default project as: ', cloud_region.config['region_name'])
  cloud['project_name'] = cloud_region.config['region_name']
os = openstack.connect(**cloud)

# ~ # OPTION-2
# ~ cloud = { 'cloud': 'otc-de' }
# ~ cloud_region = openstack.config.get_cloud_region(**cloud)
# ~ if not 'project_name' in cloud_region.config['auth']:
  # ~ cloud_region.config['auth']['project_name'] = cloud_region.config['region_name']
# ~ os = openstack.connect(config=cloud_region)


for s in os.compute.servers():
# ~ for s in os.compute.servers(all_projects=True): # all_projects doesn't seem to work on OTC
  
  print(s.name,': ', s.project_id)
  # ~ os.pprint(s)
  print('======================================================')
  
