import pkg_resources
import os
import sys
import click
import yaml
import config_modules
from utils import color_msg, Color, verify_paths, get_confirmation, create_logs_folder, logger
from config_modules.delete_resources import clean_up
# default values for the vsi on which the produced image will base upon  
DEFAULTS = {'base_image_name':'ibm-ubuntu-20-04-4-minimal-amd64-2', 'region':'us-south', 'installation_type':"Ubuntu"}

import click
@click.command()
@click.option('--output-file', '-o', help='Log of resources created by this program')
@click.option('--input-file', '-i', help=f'Template for the new configuration')
@click.option('--iam-api-key', '-a', help='IAM_API_KEY')
@click.option('--version', '-v', help=f'Get package version', is_flag=True)
@click.option('--region', help='IBM Cloud region, e.g: us-south, us-east, eu-de, eu-gb')
@click.option('--yes','-y',is_flag=True, help='Skips confirmation requests')
@click.option('--base-image-name','-im', help='Base image name')
@click.option('--installation-type','-it', help='type of CUDA installation to use, e.g. Ubuntu, Fedora, RHEL')
@click.option('--compute-iam-endpoint', help='IAM endpoint url used for compute instead of default https://iam.cloud.ibm.com')
def builder(iam_api_key, output_file, input_file, version, region, yes, base_image_name, installation_type, compute_iam_endpoint):
    create_logs_folder()

    # print(color_msg("DEBUGGING - API KEY HARDCODED", color=Color.RED))
    # iam_api_key = os.environ["RESEARCH"]

    # print(color_msg("DEBUGGING - Source file is TEST.yaml", color=Color.RED))
    test = False # affecting verify_paths()

    if version:
        print(f"{pkg_resources.get_distribution('').project_name} "
              f"{pkg_resources.get_distribution('').version}")
        exit(0)

    logger.info((color_msg("Welcome to IBM VPC Image CUDA Installer", color=Color.YELLOW)))


    # if input_file is empty, path to defaults.py is returned.
    input_file, output_file = verify_paths(input_file, output_file, test=test)
    
    with open(input_file) as f:
        base_config = yaml.safe_load(f)
    
    base_config['output_file'] = output_file

    base_config, modules = validate_api_keys(base_config, iam_api_key, compute_iam_endpoint)
    base_config['yes'] = yes

    base_config['region'] =  region if region else DEFAULTS['region']
    base_config['installation_type'] = installation_type if installation_type else DEFAULTS['installation_type']
    base_config['base_image_name'] = base_image_name if base_image_name else DEFAULTS['base_image_name']
    
    logger.info(color_msg(f"""\nBase Image Name: {base_config['base_image_name']}\nInstallation Type:{base_config['installation_type']}\nRegion:{base_config['region']} """, color=Color.YELLOW))
    if not yes:
        confirmation = get_confirmation(f"Proceed?")['answer']
        if not confirmation:
            sys.exit(0)

    for module in modules:
        next_module = module(base_config)
        try:
            base_config = next_module.run()
        except Exception as e:
            logger.critical("Exception:\n",e)
            logger.info(color_msg("Program failed, deleting created resources",color=Color.RED))
            clean_up(output_file)
            sys.exit(1)
        
    
    logger.info(color_msg(f"\nProgram Concluded.\nCreated resources are logged in {output_file}.\n", color=Color.YELLOW))

def validate_api_keys(base_config, iam_api_key, compute_iam_endpoint):
    """
    validates the api key specified.
    returns a base config dict, updated with the api-key field populated and the post api-key module removal modules list
    """
    # The API_KEY module is invoked and popped from the list. 
    modules = config_modules.MODULES
    api_key_module = modules[0]
    base_config = api_key_module(base_config).run(api_key=iam_api_key,
                                                  compute_iam_endpoint=compute_iam_endpoint)

    modules = modules[1:]
    return base_config , modules


if __name__ == "__main__":
    builder()