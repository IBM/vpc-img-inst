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
from vpc_img_inst.config_builder import ConfigBuilder, update_decorator
from vpc_img_inst.utils import password_dialog, color_msg, Color, verify_iam_api_key, store_output

class ApiKeyConfig(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.defaults['api_key'] = self.base_config['iam_api_key'] if 'iam_api_key' in self.base_config \
            else None

    @update_decorator
    def run(self, api_key=None, compute_iam_endpoint=None) -> Dict[str, Any]:

        ConfigBuilder.compute_iam_endpoint = compute_iam_endpoint
        
        if not api_key:
            default = self.defaults.get('api_key')
            api_key = password_dialog("Please provide " + color_msg("IBM API KEY", color=Color.CYAN),
                                  default=default,
                                  validate=verify_iam_api_key)['answer']

        ConfigBuilder.iam_api_key = api_key
        store_output({'iam_api_key':api_key},self.base_config)
        return api_key, compute_iam_endpoint

    def update_config(self, iam_api_key, compute_iam_endpoint=None) -> Dict[str, Any]:
        self.base_config['iam_api_key'] =  iam_api_key
        
        if compute_iam_endpoint:
            self.base_config['iam_endpoint'] =  compute_iam_endpoint
            
        return self.base_config
    
    def verify(self, base_config):
        api_key = base_config['iam_api_key']
            
        ConfigBuilder.compute_iam_endpoint = self.base_config['iam_endpoint']
        
        verify_iam_api_key(None, api_key, iam_endpoint=ConfigBuilder.compute_iam_endpoint)
        ConfigBuilder.iam_api_key = api_key
            
        return base_config