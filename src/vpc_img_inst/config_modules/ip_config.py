from vpc_img_inst.config_builder import ConfigBuilder
from typing import Any, Dict
from vpc_img_inst.utils import color_msg, Color, logger, store_output, append_random_suffix

class FloatingIpConfig(ConfigBuilder):
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.base_config = base_config
    
    def run(self) -> Dict[str, Any]:
        fip_data = self.create_ip()
        self.base_config['node_config']['ip_address'] = fip_data['address']
        self.base_config['node_config']['ip_id'] = fip_data['id']
        store_output({'ip_id':fip_data['id']},self.base_config)
        store_output({'ip_address':fip_data['address']},self.base_config)
        return self.base_config

    def create_ip(self):
        ip_name = append_random_suffix(base_name="temp-fp")
        
        floating_ip_prototype = {}
        floating_ip_prototype["name"] = ip_name
        floating_ip_prototype["zone"] = {"name": self.base_config['zone_name']}
        floating_ip_prototype["resource_group"] = {
            "id": self.base_config['node_config']["resource_group_id"]
        }

        response = self.ibm_vpc_client.create_floating_ip(floating_ip_prototype)
        floating_ip_data = response.result
        logger.info(color_msg(f"Created floating ip: {floating_ip_data['address']} with id: {floating_ip_data['id']}", color=Color.LIGHTGREEN))
        
        self.attach_ip(floating_ip_data)
        return floating_ip_data
    
    def attach_ip(self, floating_ip_data):
        # Attach the ip to the VSI's network interface
        instance_data = self.ibm_vpc_client.get_instance(self.base_config['node_config']['vsi_id']).get_result()
        try:
            self.ibm_vpc_client.add_instance_network_interface_floating_ip(
                instance_data["id"], instance_data["network_interfaces"][0]["id"], floating_ip_data["id"])
        except Exception as e:
            logger.error("Failed to attach ip to VSI's network interface\nError: ",e)
            raise
        
        return floating_ip_data['address']




