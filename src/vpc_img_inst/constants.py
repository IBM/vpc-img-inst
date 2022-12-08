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

import os
import tempfile
from pathlib import Path
DIR_PATH = os.path.dirname(os.path.realpath(__file__))  # absolute path to project's root folder.
USER_SCRIPTS_FOLDER = str(Path.home())+os.sep+".vpc-img-inst" 

DEFAULTS = {'base_image_name':'ibm-ubuntu-20-04',  
            'region':'eu-de',
             'installation_type':"ubuntu",
             "feature":"cuda", 
             "image_create_retries":3, 
             "script_inst_retries":5,
             "input_file":f'{DIR_PATH}{os.sep}defaults.yaml',
             "output_folder":tempfile.mkdtemp()}