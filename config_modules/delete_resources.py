import logging
import os
import time
from typing import Any, Dict
from config_builder import ConfigBuilder
from utils import color_msg, Color, logger
from ibm_cloud_sdk_core import ApiException

class DeleteResources(ConfigBuilder):
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.base_config = base_config

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
        print(color_msg('Deleted VM instance named: {} with id: {}'.format(instance_data['name'], instance_data['id']), color=Color.PURPLE))

        time.sleep(5)
        
        # delete subnet
        try:
            self.ibm_vpc_client.delete_subnet(self.base_config["node_config"]['subnet_id'])
        except ApiException as e:
            if e.code == 404:
                pass
            else:
                raise e
            
            time.sleep(25)
        
        print(color_msg('Deleted subnet id: {}'.format(self.base_config["node_config"]['subnet_id']), color=Color.PURPLE))
        
        # delete ssh key
        time.sleep(5)
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
        
        time.sleep(5)
        
        # delete vpc
        try:
            self.ibm_vpc_client.delete_vpc(self.base_config["node_config"]['vpc_id'])
        except ApiException as e:
            if e.code == 404:
                pass
            else:
                raise e

        print(color_msg('Deleted VPC named: {} with id: {}'.format(instance_data['vpc']['name'], self.base_config["node_config"]['vpc_id']), color=Color.PURPLE))
