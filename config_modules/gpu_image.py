from typing import Any, Dict
from config_builder import ConfigBuilder, update_decorator
from utils import password_dialog, color_msg, Color, verify_iam_api_key, get_option_from_list, free_dialog, logger
from ibm_cloud_sdk_core import ApiException
import time


class GPUImage(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self) -> Dict[str, Any]:
        instance_volume_attachments = self.ibm_vpc_client.list_instance_volume_attachments(self.base_config['node_config']['vsi_id']).get_result()
        boot_volume_id = instance_volume_attachments['volume_attachments'][0]['volume']['id']

        images = self.ibm_vpc_client.list_images().get_result()
        image_names = [image['name'] for image in images['images']]
        image_name = default_image_name = "gpu-image"

        c = 1
        while default_image_name in image_names:    # find next available vsi name
            default_image_name = f'{image_name}-{c}'
            c += 1

        self.ibm_vpc_client.create_instance_action(self.base_config['node_config']['vsi_id'], "stop")
             
        # give the instance enough time to stop before creating an image. 
        # TODO consider a better approach than sleep.   
        time.sleep(15)
        payload = {"name": default_image_name,
            "resource_group":{"id":self.base_config['node_config']['resource_group_id']},
            "source_volume": {"id": boot_volume_id}
            }      
        response = self.ibm_vpc_client.create_image(payload).result
        logger.info("response:",response)
        print(color_msg(f"Creating image: {default_image_name} with id: {response['id']}. Process may take a while, \
                            please visit the UI to track its progress. ", Color.LIGHTGREEN))

        self.base_config['new_image_id'] = response['id']
        return self.base_config


