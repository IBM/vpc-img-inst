import logging
from config_builder import ConfigBuilder
from typing import Any, Dict
from utils import free_dialog, get_option_from_list

logger = logging.getLogger(__name__)

class FloatingIpConfig(ConfigBuilder):
    
    def run(self) -> Dict[str, Any]:
        fip_address = None 
        floating_ips = self.ibm_vpc_client.list_floating_ips().get_result()['floating_ips']
        # filter away floating-ips that are already bound, or belong to a zone different than the one chosen by user  
        free_floating_ips = [ip for ip in floating_ips if not ip.get('target') and self.base_config['zone_name']==ip['zone']['name']] 

        ALLOCATE_NEW_FLOATING_IP = 'Allocate new floating ip'
        chosen_ip_data = get_option_from_list("Choose head ip", free_floating_ips, choice_key='address', do_nothing=ALLOCATE_NEW_FLOATING_IP)
        if chosen_ip_data == ALLOCATE_NEW_FLOATING_IP:
            fip_address = self.create_and_attach_ip(floating_ips)
        elif chosen_ip_data:
            fip_address = chosen_ip_data['address']
        else:
            raise Exception("IP is required to connect to the VSI")     

        self.base_config['node_config']['ip'] = fip_address
        return self.base_config

    def create_and_attach_ip(self, floating_ips):
        fip_name = free_dialog("please specify a name for your new ip address")['answer']
        fip_names = [fip['name'] for fip in floating_ips]

        default_ip_name = fip_name
        c = 1
        while default_ip_name in fip_names:    # find next available floating ip name
            default_ip_name = f'{fip_name}-{c}'
            c += 1

        floating_ip_prototype = {}
        floating_ip_prototype["name"] = default_ip_name
        floating_ip_prototype["zone"] = {"name": self.base_config['zone_name']}
        floating_ip_prototype["resource_group"] = {
            "id": self.base_config['node_config']["resource_group_id"]
        }

        response = self.ibm_vpc_client.create_floating_ip(floating_ip_prototype)
        floating_ip_data = response.result
        logger.debug(f"Created floating ip: {floating_ip_data['address']}")
        # Attach the ip to the VSI's network interface
        instance_data = self.ibm_vpc_client.get_instance(self.base_config['node_config']['vsi_id']).get_result()
        try:
            self.ibm_vpc_client.add_instance_network_interface_floating_ip(
                instance_data["id"], instance_data["network_interfaces"][0]["id"], floating_ip_data["id"])
        except Exception as e:
            logger.error("Failed to attach ip to VSI's network interface\nError: ",e)
            raise
        
        return floating_ip_data['address']




