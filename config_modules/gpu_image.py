import logging
from typing import Any, Dict
from config_builder import ConfigBuilder, update_decorator
from utils import password_dialog, color_msg, Color, verify_iam_api_key, get_option_from_list, free_dialog
from ibm_cloud_sdk_core import ApiException
logger = logging.getLogger(__name__)

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
       
        payload = {"name": default_image_name,
            "resource_group":{"id":self.base_config['node_config']['resource_group_id']},
            "source_volume": {"id": boot_volume_id}
            }      
        response = self.ibm_vpc_client.create_image(payload).result
        logger.debug("Response:\n", response)
        logger.debug("Created image ", default_image_name)
        

"""
 curl -X POST \
"https://us-south.iaas.cloud.ibm.com/v1/images?version=2022-11-01&generation=2" -H "Authorization: Bearer $TOKEN" -d '
{
        "name": "test-ifv-boot-volume",
        "source_volume": {
                "id": "r006-49a9b545-523f-441e-82d8-cfa21f159669" 
        },
        "resource_group": {
                "id": "8145289ddf7047ea93fd2835de391f43"
        }
}'

"""


# image_file_prototype_model = {}
# image_file_prototype_model['href']= 'https://us-south.iaas.cloud.ibm.com/v1/operating_systems/ubuntu-20-04-amd64'

# image_source_volume = {'source_volume':boot_volume_id}
# operating_system_identity_model = {'name':'ubuntu-20-04-amd64'}

# resource_group_identity_model = {'id':self.base_config['node_config']['resource_group_id']}


# image_prototype_model = {'name':default_image_name}
# image_prototype_model['resource_group'] = resource_group_identity_model
# # image_prototype_model['file'] = image_file_prototype_model  
# image_prototype_model['file'] = image_source_volume
# image_prototype_model['operating_system'] = operating_system_identity_model

# response = self.ibm_vpc_client.create_image(image_prototype_model).result

# payload = {"name": default_image_name,
#             "resource_group":{"id":self.base_config['node_config']['resource_group_id']},
#             "source_volume": {"id": self.base_config['node_config']['vsi_id']}
#             }  