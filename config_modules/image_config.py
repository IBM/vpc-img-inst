from config_builder import ConfigBuilder, update_decorator, spinner
from typing import Any, Dict
from utils import logger



class ImageConfig(ConfigBuilder):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self) -> Dict[str, Any]:

        @spinner
        def get_image_objects():
            return self.ibm_vpc_client.list_images().get_result()['images']
            
        image_objects = get_image_objects()
        image = next((obj for obj in image_objects if 'ibm-ubuntu-20-04-' in obj['name']), None)
        self.base_config['node_config']['image_id'] = image['id']
        self.base_config['node_config']['image_name'] = image['name']
        self.base_config['node_config']['boot_volume_capacity'] = self.base_config['node_config'].get("boot_volume_capacity", 100)

        logger.info(f"image Chosen: {image['name']}")
        return self.base_config
