import openstack
import yaml

def check(**kwargs):
  cloud_region = openstack.config.get_cloud_region(**kwargs)
  print('name: ', cloud_region.name)
  print(' full_name: ', cloud_region.full_name)
  print(' region_name: ', cloud_region.get_region_name())
  if 'project_name' in cloud_region.config['auth']:
    print(' Project Name: ', cloud_region.config['auth']['project_name'])
  # ~ print(yaml.dump([cloud_region.config]))
  

check(cloud = 'otc')
check(cloud = 'otc-none')
check(cloud = 'otc-de')
check(cloud = 'otc-de', project_name = 'eu-de_shared1')


# need to provide cloud and region... use region as project name
# another option, cloud.yaml contains region, and use region as project name

# ~ print('cloud names: ',openstack.config.cloud_config.cloud_names())

# ~ def get_one(self, cloud=None, validate=True, argparse=None, **kwargs):
        # ~ """Retrieve a single CloudRegion and merge additional options

        # ~ :param string cloud:
            # ~ The name of the configuration to load from clouds.yaml
        # ~ :param boolean validate:
            # ~ Validate the config. Setting this to False causes no auth plugin
            # ~ to be created. It's really only useful for testing.
        # ~ :param Namespace argparse:
            # ~ An argparse Namespace object; allows direct passing in of
            # ~ argparse options to be added to the cloud config.  Values
            # ~ of None and '' will be removed.
        # ~ :param region_name: Name of the region of the cloud.
        # ~ :param kwargs: Additional configuration options

        # ~ :returns: openstack.config.cloud_region.CloudRegion
        # ~ :raises: keystoneauth1.exceptions.MissingRequiredOptions
            # ~ on missing required auth parameters
        # ~ """
        
            # ~ def get_cloud_names(self):
        # ~ return self.cloud_config['clouds'].keys()
