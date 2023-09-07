import openstack
from datetime import datetime


# ~ os = openstack.connect(cloud='otc')
# ~ os = openstack.connect(cloud='otc-de-shared1')
os = openstack.connect(cloud='otc-test')


for p in os.list_projects():
  print(p['name'])
  # ~ os.pprint(p)
  # ~ print('======')
  # ~ usage=os.get_compute_usage(p['name'], start=datetime.strptime("2023-01-01","%Y-%m-%d"), end=datetime.strptime("2023-09-01","%Y-%m-%d"))
  # ~ os.pprint(usage)
  print('======================================================')
  
  # ~ otc-de-shared1:
