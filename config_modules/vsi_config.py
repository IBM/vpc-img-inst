from typing import Any, Dict
from config_builder import ConfigBuilder
from utils import color_msg, Color, logger, get_unique_name, store_output
from ibm_cloud_sdk_core import ApiException

class VSIConfig(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self) -> Dict[str, Any]:
        selected_vsi = self.get_vsi()

        self.base_config['node_config']['vsi_id'] = selected_vsi['id']
        store_output({'vsi_id':selected_vsi['id']},self.base_config)
        return self.base_config


    def get_vsi(self):
        res = self.ibm_vpc_client.list_instances(vpc_id=self.base_config['node_config']['vpc_id'],
                                        resource_group_id=self.base_config['node_config']['resource_group_id']).get_result()
        server_instances = [{'name':vsi['name'], "data": vsi} for vsi in res['instances']]   
        return self.create_new_instance(server_instances)
     
    
    def create_new_instance(self, server_instances):
        security_group_identity_model = {"id": self.base_config["node_config"]["security_group_id"]}
        subnet_identity_model = {"id": self.base_config["node_config"]["subnet_id"]}
        primary_network_interface = {
            "name": "eth0",
            "subnet": subnet_identity_model,
            "security_groups": [security_group_identity_model],
        }
        vsi_name = get_unique_name(name = "temp-vsi", name_list = [vsi['name'] for vsi in server_instances])

        boot_volume_profile = {
            "capacity": self.base_config["node_config"]["boot_volume_capacity"] if self.base_config["node_config"]["boot_volume_capacity"] else 100,
            "name": "{}-boot".format(vsi_name),
            "profile": {
                "name": self.base_config["node_config"].get("volume_tier_name", "general-purpose")
            },
        }

        boot_volume_attachment = {
            "delete_volume_on_instance_delete": True,
            "volume": boot_volume_profile,
        }

        key_identity_model = {"id": self.base_config["node_config"]["key_id"]}
        profile_name = self.base_config["node_config"]["instance_profile_name"]
        profile_name = "bx2-2x8" if not profile_name else profile_name

        instance_prototype = {}
        instance_prototype["name"] = vsi_name
        instance_prototype["keys"] = [key_identity_model]
        instance_prototype["profile"] = {"name": profile_name}
        instance_prototype["resource_group"] = {"id": self.base_config["node_config"]["resource_group_id"]}
        instance_prototype["vpc"] = {"id": self.base_config["node_config"]["vpc_id"]}
        instance_prototype["image"] = {"id": self.base_config["node_config"]["image_id"]}

        instance_prototype["zone"] = {"name": self.base_config["zone_name"]}
        instance_prototype["boot_volume_attachment"] = boot_volume_attachment
        instance_prototype["primary_network_interface"] = primary_network_interface

        try:
            resp = self.ibm_vpc_client.create_instance(instance_prototype).result
        except ApiException as e:
            if e.code == 400 and "already exists" in e.message:
                logger.error("VSI already exists")
            elif e.code == 400 and "over quota" in e.message:
                logger.error("Create VM instance {} failed due to quota limit")
            else:
                logger.error(
                    "Create VM instance failed with status code {}".format(
                         str(e.code)
                    )
                )
            raise e

        print(color_msg(f"Created VM instance: {vsi_name} with id: {resp['id']}",color=Color.LIGHTGREEN))
        return resp
