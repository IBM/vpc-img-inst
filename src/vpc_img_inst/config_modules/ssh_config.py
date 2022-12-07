import os
import subprocess
from typing import Any, Dict
from pathlib import Path
from inquirer import errors
from vpc_img_inst.config_builder import ConfigBuilder, spinner
from vpc_img_inst.utils import Color, color_msg, get_unique_file_name,logger, append_random_suffix, store_output
from ibm_cloud_sdk_core import ApiException
DEFAULT_KEY_NAME = 'temp'
        
def generate_keypair():
    """Returns newly generated public ssh-key's contents and private key's path"""
    key_name= f"id_rsa.{DEFAULT_KEY_NAME}"
    home = str(Path.home())
    ssh_folder_path = f"{home}{os.sep}.ssh{os.sep}"
    unique_file_name = get_unique_file_name(key_name,ssh_folder_path)

    os.system(f'ssh-keygen -b 2048 -t rsa -f {unique_file_name} -q -N ""')

    logger.info(color_msg(f"Generated private key: {os.path.abspath(unique_file_name)}",color=Color.LIGHTGREEN))
    logger.info(color_msg(f"Generated public key: {os.path.abspath(unique_file_name)}.pub",color=Color.LIGHTGREEN))

    with open(f"{unique_file_name}.pub", 'r') as file:
        ssh_key_data = file.read()
    ssh_key_path = os.path.abspath(unique_file_name)
    return ssh_key_data, ssh_key_path

def get_ssh_key(ibm_vpc_client, name):
    """Returns ssh key matching specified name, stored in the VPC associated with the vpc_client"""
    for key in ibm_vpc_client.list_keys().result['keys']:
        if key['name'] == name:
            return key
                    
def register_ssh_key(ibm_vpc_client, config):
    """Returns the key's name on the VPC platform, it's public key's contents and the local path to it.
        Registers an either existing or newly generated ssh-key to a specific VPC. """
    resource_group_id = config['node_config']['resource_group_id']
    unique_key_name = append_random_suffix(base_name=DEFAULT_KEY_NAME)
    ssh_key_data, ssh_key_path = generate_keypair()

    response = None
    try:    # regardless of the above, try registering an ssh-key 
        response = ibm_vpc_client.create_key(public_key=ssh_key_data, name=unique_key_name, resource_group={
                                        "id": resource_group_id}, type='rsa')
    except ApiException as e:
        print(e)
        if "Key with fingerprint already exists" in e.message:
            logger.info(color_msg("Can't register an SSH key with the same fingerprint",Color.RED))
        raise # can't continue the configuration process without a valid ssh key     
        
    result = response.get_result()
    logger.info(color_msg(f"Registered SSH key: {unique_key_name} with id: {result['id']} to resource group\n",Color.LIGHTGREEN))
    return result['name'], result['id'], ssh_key_path

class SshKeyConfig(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.base_config = base_config

    def _validate_keypair(self, answers, current):
        if not current or not os.path.exists(os.path.abspath(os.path.expanduser(current))):
            raise errors.ValidationError(
            '', reason=f"File {current} doesn't exist")

        public_res = self.ibm_vpc_client.get_key(self.ssh_key_id).get_result()['public_key'].split(' ')[1]
        private_res = subprocess.getoutput([f"ssh-keygen -y -f {current} | cut -d' ' -f 2"])

        if not public_res == private_res:
            raise errors.ValidationError(
            '', reason=f"Private ssh key {current} and public key {self.ssh_key_name} are not a pair")

        return public_res == private_res
    
    @spinner
    def get_ssh_key_names(self):
        return [key['name'] for key in self.ibm_vpc_client.list_keys().get_result()['keys']]

    def run(self) -> Dict[str, Any]:
        ssh_key_name, ssh_key_id, ssh_key_path = register_ssh_key(self.ibm_vpc_client, self.base_config)
        self.ssh_key_id = ssh_key_id
        self.ssh_key_name = ssh_key_name

        self.base_config['node_config']['key_id'] = ssh_key_id
        self.base_config['auth']['ssh_user'] = 'root' # user is hardcoded to root 
        self.base_config['auth']['ssh_private_key'] = ssh_key_path
        store_output({'ssh_private_key':ssh_key_path},self.base_config)
        store_output({'key_id':ssh_key_id},self.base_config)
        return self.base_config