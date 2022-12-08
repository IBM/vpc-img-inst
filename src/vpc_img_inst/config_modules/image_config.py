# (C) Copyright IBM Corp. 2022.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Dict
from vpc_img_inst.config_builder import ConfigBuilder, update_decorator, spinner
from vpc_img_inst.utils import logger, color_msg, Color, CACHE



class ImageConfig(ConfigBuilder):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    @spinner
    def get_image_objects(self):
        images = []
        res = self.ibm_vpc_client.list_images().get_result()
        images.extend(res['images'])

        while res.get('next',None):
            link_to_next = res['next']['href'].split('start=')[1].split('&limit')[0]
            res = self.ibm_vpc_client.list_images(start=link_to_next).get_result()
            images.extend(res['images'])
        return images

    def run(self) -> Dict[str, Any]:
        image_objects = self.get_image_objects()
        # picks the first image with AMD architecture (opposed to s390x) that contains prefix matching user's input (-im flag).   
        image = next((img for img in image_objects if img['name'].startswith(self.base_config['user_image_name']) \
            and img['operating_system']['architecture'].startswith('amd')), None)
        
        if not image:
            logger.critical(color_msg(f"Base image chosen: {self.base_config['user_image_name']} doesn't exist. ",color=Color.RED))
            raise Exception
            
        self.base_config['node_config']['image_id'] = image['id']
        self.base_config['node_config']['image_name'] = image['name']
        self.base_config['node_config']['boot_volume_capacity'] = self.base_config['node_config'].get("boot_volume_capacity", 100)

        logger.info(f"image Chosen: {image['name']}")
        return self.base_config


