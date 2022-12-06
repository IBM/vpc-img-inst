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
             "script_inst_retries":3,
             "input_file":f'{DIR_PATH}{os.sep}defaults.yaml',
             "output_folder":tempfile.mkdtemp()}