import sys
from vpc_img_inst.config_builder import ConfigBuilder, update_decorator, spinner
from typing import Any, Dict
from vpc_img_inst.utils import logger,color_msg,Color, store_output


class EndpointConfig(ConfigBuilder):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        
    @spinner
    def _get_regions_objects(self):
        return self.ibm_vpc_client.list_regions().get_result()['regions']
        
    @update_decorator
    def run(self) -> Dict[str, Any]:
        regions_objects = self._get_regions_objects()
        region_obj = next((r for r in regions_objects if r['name'] == self.base_config['region']), None)
        if not region_obj:
             logger.critical(color_msg(f"Region Chosen: {self.region} is invalid ",color=Color.RED))
             raise Exception("Invalid argument")
        self.ibm_vpc_client.set_service_url(region_obj['endpoint'] + '/v1')   # update global ibm_vpc_client to selected endpoint
        ConfigBuilder.region = region_obj['name']
        store_output({'endpoint':region_obj['endpoint']},self.base_config)  # to enable user to manually execute the clean-up module at a later time.  
        
        logger.info(f"Region Chosen: {region_obj['name']} ")
        return region_obj['endpoint']

    def update_config(self, endpoint):
        self.base_config['endpoint'] = endpoint
        self.base_config['region'] = ConfigBuilder.region



