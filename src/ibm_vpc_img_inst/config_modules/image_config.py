from typing import Any, Dict
from ibm_vpc_img_inst.config_builder import ConfigBuilder, update_decorator, spinner
from ibm_vpc_img_inst.utils import logger, color_msg, Color



class ImageConfig(ConfigBuilder):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self) -> Dict[str, Any]:

        @spinner
        def get_image_objects():
            return self.ibm_vpc_client.list_images().get_result()['images']
            
        image_objects = get_image_objects()
        image = next((obj for obj in image_objects if obj['name'].startswith(self.base_config['base_image_name'])), None)
        if not image:
            logger.critical(color_msg(f"Base image chosen: {self.base_config['base_image_name']} doesn't exist. ",color=Color.RED))
            raise Exception
        self.base_config['node_config']['image_id'] = image['id']
        self.base_config['node_config']['image_name'] = image['name']
        self.base_config['node_config']['boot_volume_capacity'] = self.base_config['node_config'].get("boot_volume_capacity", 100)

        logger.info(f"image Chosen: {image['name']}")
        return self.base_config
