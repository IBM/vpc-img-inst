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



