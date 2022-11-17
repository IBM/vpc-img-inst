import os
DIR_PATH = os.path.dirname(os.path.realpath(__file__))  # absolute path to project's root folder.
DEFAULTS = {'base_image_name':'ibm-ubuntu-20-04-4-minimal-amd64-2',  
            'region':'us-south',
             'installation_type':"Ubuntu",
             "feature":"CUDA", 
             "image_create_retries":3, 
             "script_inst_retries":3,
             "input_file":f'{DIR_PATH}{os.sep}defaults.yaml',
             "output_folder":f"{DIR_PATH}{os.sep}logs{os.sep}"}