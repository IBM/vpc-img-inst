import logging
import os
import time
import yaml
import sys
from typing import Any, Dict
sys.path.append('../generate_gpu_image')
from config_builder import ConfigBuilder, spinner
from utils import color_msg, Color, logger
from ibm_cloud_sdk_core import ApiException

class DeleteResources(ConfigBuilder):
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.base_config = base_config
        if 'delete_resources' in base_config:
            self.delete_config()

    def run(self) -> Dict[str, Any]:
        self.delete_config()
        return self.base_config

    def delete_config(self):

        instance_data = self.ibm_vpc_client.get_instance(self.base_config['node_config']['vsi_id']).get_result()

        interface_id = instance_data['network_interfaces'][0]['id']
        fips = self.ibm_vpc_client.list_instance_network_interface_floating_ips(
                    instance_data['id'], interface_id).get_result()['floating_ips']
        if fips:
            fip = fips[0]['id']
            self.ibm_vpc_client.delete_floating_ip(fip)

            print(color_msg('\n\nDeleted ip named: {} of address: {}'.format(fips[0]['name'], self.base_config['node_config']['ip']), color=Color.PURPLE))

        # delete instance
        self.ibm_vpc_client.delete_instance(instance_data['id'])   
        # blocking call
        res=self.poll_instance_exists(instance_data['id'], instance_data['name'])

        # delete subnet
        self.ibm_vpc_client.delete_subnet(self.base_config["node_config"]['subnet_id'])
        self.poll_subnet_exists(self.base_config["node_config"]['subnet_id'])

        # delete ssh key
        try:
            self.ibm_vpc_client.delete_key(id=self.base_config["node_config"]['key_id'])
        except ApiException as e:
            if e.code == 404:
                pass
            else:
                raise e
        print(color_msg(f'Removed SSH key id: {self.base_config["node_config"]["key_id"]} from resource group', color=Color.PURPLE))

        private_key = os.path.expanduser(self.base_config['auth']['ssh_private_key'])
        try:
            os.remove(private_key)
            print(color_msg(f'Deleted private_key: {private_key}', color=Color.PURPLE))
        except OSError as e:
            print(color_msg("Failed to delete {private_key}"),Color.RED)
            print(e)
        
        public_key = private_key+".pub"
        try:
            os.remove(public_key)
            print(color_msg(f'Deleted private_key: {public_key}', color=Color.PURPLE))
        except OSError as e:
            print(color_msg("Failed to delete {public_key}"),Color.RED)
            print(e)
        
        # delete vpc
        try:
            self.ibm_vpc_client.delete_vpc(self.base_config["node_config"]['vpc_id'])
        except ApiException as e:
            if e.code == 404:
                pass
            else:
                raise e

        print(color_msg('Deleted VPC named: {} with id: {}'.format(instance_data['vpc']['name'], self.base_config["node_config"]['vpc_id']), color=Color.PURPLE))

    @spinner
    def poll_instance_exists(self,instance_id,instance_name):
        tries = 30 # waits up to 1 min with 2 sec interval
        sleep_interval = 2
        msg = ""
        while tries:
            try:
                instance_data = self.ibm_vpc_client.get_instance(instance_id).result
            except:
                print(color_msg('Deleted VM instance named: {} with id: {}'.format(instance_name, instance_id), color=Color.PURPLE))
                return True
            
            #print("Retrying... current status:", instance_data['status'])
            tries -= 1
            time.sleep(sleep_interval)
        print(f"\Failed to delete instance within expected time frame of {tries*sleep_interval/60} minutes.\n")
        return False

    @spinner
    def poll_subnet_exists(self,subnet_id):
        tries = 30 # waits up to 1 min with 2 sec interval
        sleep_interval = 2
        msg = ""
        while tries:
            try:
                subnet_data = self.ibm_vpc_client.get_instance(subnet_id).result
            except:
                print(color_msg('Deleted subnet id: {}'.format(self.base_config["node_config"]['subnet_id']), color=Color.PURPLE))
                return True
            
            #print("Retrying... current status:", subnet_data['status'])
            tries -= 1
            time.sleep(sleep_interval)
        print(f"\Failed to delete instance within expected time frame of {tries*sleep_interval/60} minutes.\n")
        return False


if __name__ == "__main__":
    base_config = {'delete_resources':True}
    
    output_file = "/home/omer/dev1/generate_gpu_image/created_resources"
    with open(output_file, 'r') as f:
        resources = yaml.safe_load(f)
    
    node_config={"node_config":{"subnet_id":resources['subnet_id' if 'subnet_id' in resources else ''],
                                 "vpc_id":resources['vpc_id'] if 'vpc_id' in resources else '',
                                 "vsi_id":resources['vsi_id'] if 'vsi_id' in resources else '',
                                 "key_id":resources['key_id'] if 'key_id' in resources else '',
                                  "ip": resources['ip'] if 'ip' in resources else '' }
                }
    auth = {"auth":{"ssh_private_key":resources['ssh_private_key'] if 'ssh_private_key' in resources else ''}}
    base_config.update({"iam_api_key": resources['iam_api_key']})
    base_config.update(auth)
    base_config.update(node_config)


    # for manual use:

    # api_key = os.environ['RESEARCH']
    # base_config.update({"iam_api_key": api_key})
    # node_config={"node_config":{"subnet_id":"",
    #                              "vpc_id":"",
    #                              "vsi_id":"",
    #                              "key_id":"",
    #                              "ip":""}
    #             }
    # auth = {"auth":{"ssh_private_key":""}}
    # base_config.update(node_config)
    # base_config.update(auth)


    obj = DeleteResources(base_config)

    if 'ip' in resources:
        pass
    if 'key_id' in resources:
        pass
    if 'vsi_id' in resources:
        pass
    if 'vpc_id' in resources:
        pass
    if 'ssh_private_key' in resources:
        pass
    if 'subnet_id' in resources:
        pass