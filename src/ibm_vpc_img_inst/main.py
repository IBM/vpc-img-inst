import os
import sys

import click
import pkg_resources
import yaml
from ibm_vpc_img_inst import config_modules
from ibm_vpc_img_inst.config_modules.delete_resources import clean_up
from ibm_vpc_img_inst.constants import DEFAULTS

from ibm_vpc_img_inst.utils import (Color, color_msg, create_logs_folder,
                                    get_confirmation, logger, verify_paths,
                                    get_installation_types_for_feature,get_supported_features)

@click.command()
@click.option('--output-folder', '-o', show_default=True, default=DEFAULTS['output_folder'], help='Path to folder storing IDs of resources created by this program and installation logs')
@click.option('--input-file', '-i',show_default=True, default=DEFAULTS['input_file'], help=f'Template for the new configuration')
@click.option('--iam-api-key', '-a', help='IAM_API_KEY')
@click.option('--version', '-v', help=f'Get package version', is_flag=True)
@click.option('--region','-r', show_default=True, default=DEFAULTS['region'], help='IBM Cloud region, e.g: us-south, us-east, eu-de, eu-gb.')
@click.option('--yes','-y',show_default=True, is_flag=True, help='Skips confirmation requests')
@click.option('--base-image-name','-im', show_default=True, default=DEFAULTS['base_image_name'], help='Prefix of image names from your account, on which the produced image will be based')
@click.option('--installation-type','-it',show_default=True, default=DEFAULTS['installation_type'], help='type of installation to use, e.g. for feature CUDA the currently supported types are: Ubuntu and RHEL.')
@click.option('--feature','-f', show_default=True, default=DEFAULTS['feature'], help='Feature to install on the produced image. Currently: CUDA or Docker.')
@click.option('--compute-iam-endpoint', help='IAM endpoint url used for compute instead of default https://iam.cloud.ibm.com')
def builder(iam_api_key, output_folder, input_file, version, region, yes, base_image_name, installation_type, feature, compute_iam_endpoint):
    create_logs_folder(output_folder)

    if version:
        print(f"{pkg_resources.get_distribution('ibm-vpc-img-inst').project_name}"
              f"{pkg_resources.get_distribution('ibm-vpc-img-inst').version}")
        exit(0)

    logger.info((color_msg("Welcome to IBM VPC Image Installer", color=Color.YELLOW)))

    # if input_file is empty, path to defaults.py is returned.
    input_file, output_file = verify_paths(input_file, output_folder)
    
    with open(input_file) as f:
        base_config = yaml.safe_load(f)
    
    base_config['output_folder'] = output_file[:output_file.rfind(os.sep)+1]
    base_config['output_file'] = output_file

    base_config, modules = validate_api_keys(base_config, iam_api_key, compute_iam_endpoint)
    base_config['yes'] = yes

    base_config['region'] =  region.lower() 
    base_config['installation_type'] = installation_type.lower() 
    base_config['user_image_name'] = base_image_name.lower() 
    base_config['feature'] = feature.lower() 

    logger.info(color_msg(f"""\n\nBase Image Name: {base_config['user_image_name']}\nFeature: {base_config['feature']}\nInstallation Type: {base_config['installation_type']}\nRegion: {base_config['region']}\nImage Creation Retries: {DEFAULTS['image_create_retries']} """, color=Color.YELLOW))
    if not yes:
        confirmation = get_confirmation(f"Proceed?")['answer']
        if not confirmation:
            sys.exit(0)

    validate_flags(base_config['feature'],base_config['installation_type'])

    for module in modules:
        next_module = module(base_config)
        try:
            base_config = next_module.run()
        except Exception as e:
            logger.critical(f"Exception:\n{e}")
            logger.info(color_msg("Program failed. Deleting created resources",color=Color.RED))
            clean_up(output_file)
            sys.exit(1)
        
    
    logger.info(color_msg(f"\n\nProgram Concluded.\nCreated resources are logged in {output_file}.\n", color=Color.YELLOW))

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

def validate_flags(feature,installation_type):
    features = get_supported_features()
    if feature not in features:
        logger.critical(color_msg(f"Feature Chosen: {feature} isn't supported ",color=Color.RED))
        raise Exception("Invalid argument.")

    if installation_type not in get_installation_types_for_feature(feature):
        logger.critical(color_msg(f"Installation type Chosen: {installation_type} isn't supported for feature: {feature}",color=Color.RED))
        raise Exception("Invalid argument.")


if __name__ == "__main__":
    builder()