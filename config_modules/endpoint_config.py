import logging
from config_builder import ConfigBuilder, update_decorator, spinner
from typing import Any, Dict
from utils import color_msg, Color, logger, get_option_from_list


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
        ConfigBuilder.ibm_vpc_client.set_service_url(region_obj['endpoint'] + '/v1')   # update global ibm_vpc_client to selected endpoint
        ConfigBuilder.region = region_obj['name']
        
        logger.info(f"Region Chosen: {region_obj['name']} ")
        return region_obj['endpoint']

    def update_config(self, endpoint):
        self.base_config['endpoint'] = endpoint
        self.base_config['region'] = ConfigBuilder.region



