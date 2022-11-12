import logging
import os
import time
import yaml
import sys
from typing import Any, Dict
sys.path.append('../generate_gpu_image')
from config_builder import ConfigBuilder, spinner
from utils import color_msg, Color, logger, DIR_PATH
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
        print("---------------------------------------------")

        if 'ip_id' in self.base_config['node_config'] and self.base_config['node_config']['ip_id']:
            try:
                self.ibm_vpc_client.delete_floating_ip(self.base_config['node_config']['ip_id'])
                logger.info(color_msg(f"""Deleted ip id: {self.base_config['node_config']['ip_id']} of address: {self.base_config['node_config']['ip_address']}""", color=Color.PURPLE))
            except ApiException as e:
                if e.code == 404:  # resource was already deleted
                    logger.info(f"""Floating ip with id: "{self.base_config['node_config']['ip_id']}" of address "{self.base_config['node_config']['ip_address']}" doesn't exist""")
                else:
                    raise e

        if 'vsi_id' in self.base_config['node_config'] and self.base_config['node_config']['vsi_id']:    
            # instance_data = self.ibm_vpc_client.get_instance(self.base_config['node_config']['vsi_id']).get_result()
        # delete instance
            try:
                self.ibm_vpc_client.delete_instance(self.base_config['node_config']['vsi_id'])  
                # blocking call waiting for instance to delete. 
                res=self.poll_instance_exists(self.base_config['node_config']['vsi_id']) 
            except ApiException as e:
                if e.code == 404:  # resource was already deleted
                    logger.info(f"""VSI with id: "{self.base_config['node_config']['vsi_id']}" doesn't exist""")
                else:
                    raise e            
        

        # delete subnet
        if 'subnet_id' in self.base_config["node_config"] and self.base_config["node_config"]['subnet_id']:
            try:
                self.ibm_vpc_client.delete_subnet(self.base_config["node_config"]['subnet_id'])
                # blocking call waiting for subnet to delete.
                self.poll_subnet_exists(self.base_config["node_config"]['subnet_id'])
            except ApiException as e:
                if e.code == 404:  # resource was already deleted
                    logger.info(f"""Subnet with id: "{self.base_config["node_config"]['subnet_id']}" doesn't exist""")
                else:
                    raise e
            
        # delete ssh key
        if 'key_id' in self.base_config["node_config"] and self.base_config["node_config"]['key_id']:
            try:
                self.ibm_vpc_client.delete_key(id=self.base_config["node_config"]['key_id'])
                logger.info(color_msg(f'Removed SSH key id: {self.base_config["node_config"]["key_id"]} from resource group', color=Color.PURPLE))
            except ApiException as e:
                if e.code == 404:
                    logger.info(f"""SSH key with id: "{self.base_config["node_config"]["key_id"]}" doesn't exist""")
                else:
                    raise e
            
        if 'ssh_private_key' in self.base_config['auth'] and self.base_config['auth']['ssh_private_key']:
            private_key = os.path.expanduser(self.base_config['auth']['ssh_private_key'])
            try:
                os.remove(private_key)
                logger.info(color_msg(f'Deleted private key: {private_key}', color=Color.PURPLE))
            except OSError as e:
                logger.info(f"""Local private key: {private_key} doesn't exist""")
            
            public_key = private_key+".pub"
            try:
                os.remove(public_key)
                logger.info(color_msg(f'Deleted public key: {public_key}', color=Color.PURPLE))
            except OSError as e:
                logger.info(f"""Local public key: {public_key} doesn't exist""")
        
        # delete vpc
        if 'vpc_id' in self.base_config["node_config"] and self.base_config["node_config"]['vpc_id']:
            try:
                self.ibm_vpc_client.delete_vpc(self.base_config["node_config"]['vpc_id'])
                logger.info(color_msg('Deleted VPC with id: {}'.format(self.base_config["node_config"]['vpc_id']), color=Color.PURPLE))
            except ApiException as e:
                if e.code == 404:
                    logger.info(f"""VPC with id: "{self.base_config["node_config"]['vpc_id']}" doesn't exist""")
                else:
                    raise e

        # delete failed images
        failed_images = _get_failed_images(self.base_config['output_file'])
        for failed_image_id in failed_images:
            try:
                self.ibm_vpc_client.delete_image(failed_image_id)
                logger.info(color_msg('Deleted failed image with id: {}'.format(failed_image_id), color=Color.PURPLE))
            except ApiException as e:
                if e.code == 404:  # resource was already deleted
                    pass
                else:
                    raise e            


    def poll_instance_exists(self,instance_id):
        tries = 30 # waits up to 1 min with 2 sec interval
        sleep_interval = 2
        msg = ""
        while tries:
            try:
                instance_data = self.ibm_vpc_client.get_instance(instance_id).result
            except Exception:
                logger.info(color_msg('Deleted VM instance with id: {}'.format(instance_id), color=Color.PURPLE))
                return True
            
            #print("Retrying... current status:", instance_data['status'])
            tries -= 1
            time.sleep(sleep_interval)
        logger.info(f"\Failed to delete instance within expected time frame of {tries*sleep_interval/60} minutes.\n")
        return False

    def poll_subnet_exists(self,subnet_id):
        tries = 30 # waits up to 1 min with 2 sec interval
        sleep_interval = 4
        msg = ""
        while tries:
            try:
                subnet_data = self.ibm_vpc_client.get_instance(subnet_id).result
                print(subnet_data)
            except Exception:
                logger.info(color_msg('Deleted subnet id: {}'.format(self.base_config["node_config"]['subnet_id']), color=Color.PURPLE))
                return True
            
            #print("Retrying... current status:", subnet_data['status'])
            tries -= 1
            time.sleep(sleep_interval)
        logger.info(f"\Failed to delete instance within expected time frame of {tries*sleep_interval/60} minutes.\n")
        return False


def clean_up(input_file=None):
    base_config = {'delete_resources':True}
    
    file = input_file if input_file else f"{DIR_PATH}{os.sep}logs{os.sep}created_resources-11"
    base_config['output_file'] = file
    with open(file, 'r') as f:
        resources = yaml.safe_load(f)
    
    node_config={"node_config":{"subnet_id":resources['subnet_id'] if 'subnet_id' in resources else '',
                                 "vpc_id":resources['vpc_id'] if 'vpc_id' in resources else '',
                                 "vsi_id":resources['vsi_id'] if 'vsi_id' in resources else '',
                                 "key_id":resources['key_id'] if 'key_id' in resources else '',
                                  "ip_id": resources['ip_id'] if 'ip_id' in resources else '' ,
                                  "ip_address": resources['ip_address'] if 'ip_address' in resources else '' ,}
                }
    auth = {"auth":{"ssh_private_key":resources['ssh_private_key'] if 'ssh_private_key' in resources else ''}}

    base_config.update({"iam_api_key": resources['iam_api_key']})
    base_config.update(auth)
    base_config.update(node_config)
    # __init__ of DeleteResources starts the clean-up process when this module is run independently.     
    obj = DeleteResources(base_config)  

def _get_failed_images(file):
    failed_images = []

    if not os.path.isfile(file):
        logger.error(color_msg("Failed to fetch failed images. Resources file doesn't exist",color=Color.RED))
        return failed_images
    else:
        with open(file, 'r') as f:
            resources = yaml.safe_load(f)
    
    for resource_key in resources:
        if 'failed_image' in resource_key:  # failed images are keys in the format: failed_image_<NUMBER>
            failed_images.append(resources[resource_key]['image_id'])
    return failed_images


if __name__ == "__main__":
    resources_file = None
    if len(sys.argv)>1:
        resources_file = sys.argv[1]
    if resources_file and not os.path.exists(os.path.abspath(os.path.expanduser(resources_file))):
        logger.critical(color_msg(f"file {resources_file} doesn't exist in path",color=Color.RED))
        sys.exit(1)
    clean_up(resources_file)