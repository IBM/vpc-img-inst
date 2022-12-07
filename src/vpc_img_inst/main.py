import os
import sys
import click
import pkg_resources
import yaml
from vpc_img_inst import config_modules
from vpc_img_inst.config_modules.delete_resources import clean_up
from vpc_img_inst.constants import DEFAULTS

from vpc_img_inst.utils import (Color, color_msg, create_folders,
                                    get_confirmation, logger, verify_paths,
                                    get_installation_types_for_feature,get_supported_features)

@click.command()
@click.option('--output-folder', '-o', show_default=True, default=DEFAULTS['output_folder'], help='Path to folder storing IDs of resources created by this program and installation logs')
@click.option('--iam-api-key', '-a', help='IAM_API_KEY')
@click.option('--version', '-v', help=f'Get package version', is_flag=True)
@click.option('--region','-r', show_default=True, default=DEFAULTS['region'], help='IBM Cloud region, e.g: us-south, us-east, eu-de, eu-gb.')
@click.option('--yes','-y',show_default=True, is_flag=True, help='Skips confirmation requests')
@click.option('--base-image-name','-im', show_default=True, default=DEFAULTS['base_image_name'], help='Prefix of image names from your account, on which the produced image will be based')
@click.option('--installation-type','-it',show_default=True, default=DEFAULTS['installation_type'], help='type of installation to use, e.g. for feature "cuda" the currently supported types are: "ubuntu" and "rhel".')
@click.option('--feature','-f', show_default=True,default=[DEFAULTS['feature']], multiple=True, help='Feature to install on the produced image. Currently: "cuda" or "docker".')
@click.option('--cleanup','-c', show_default=True, default=None, help='Path to a resources file, that will be submitted for deletion. Program will be terminated subsequently.')
@click.option('--compute-iam-endpoint', help='IAM endpoint url used for compute instead of default https://iam.cloud.ibm.com')
def builder(iam_api_key, output_folder, version, region, yes, base_image_name, installation_type, feature, cleanup, compute_iam_endpoint):
    if cleanup:
        clean_up(cleanup)
        exit(0)

    if version:
        print(f"{pkg_resources.get_distribution('vpc-img-inst').project_name}"
              f"-{pkg_resources.get_distribution('vpc-img-inst').version}")
        exit(0)

    logger.info((color_msg("VPC Image Installer Starting...", color=Color.YELLOW)))

    create_folders() # creates user scripts folder if does not exist

    # if input_file is empty, path to defaults.py is returned.
    input_file, output_file = verify_paths("", output_folder)
    
    with open(input_file) as f:
        base_config = yaml.safe_load(f)
    
    base_config['output_folder'] = output_file[:output_file.rfind(os.sep)+1]
    base_config['output_file'] = output_file

    base_config, modules = validate_api_keys(base_config, iam_api_key, compute_iam_endpoint)
    base_config['yes'] = yes

    base_config['region'] =  region.lower() 
    base_config['installation_type'] = installation_type
    base_config['user_image_name'] = base_image_name
    base_config['feature'] = feature
    
    logger.info(color_msg(f"""\n\nBase Image Name: {base_config['user_image_name']}\nFeature: {','.join(feature)}\nInstallation Type: {base_config['installation_type']}\nRegion: {base_config['region']}\nImage Creation Retries: {DEFAULTS['image_create_retries']} """, color=Color.YELLOW))
    logger.info(color_msg(f"\n\nCreated resources will be logged in {output_file}.\n", color=Color.YELLOW))
    if not yes:
        confirmation = get_confirmation(f"Proceed?")['answer']
        if not confirmation:
            sys.exit(0)

    base_config['scripts_path']=get_scripts_path(base_config['feature'],base_config['installation_type'])

    for module in modules:
        next_module = module(base_config)
        try:
            base_config = next_module.run()
        except Exception as e:
            logger.critical(f"Exception in {next_module.__class__.__name__} \n{e}")
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

def get_scripts_path(features,installation_type):
    """returns script path to execute in case both the specified feature exists and the installation type exits for it"""
    scripts = []
    supported_features = get_supported_features()
    for feature in features:
        
        if feature not in supported_features:
            logger.critical(color_msg(f"Feature Chosen: {feature} isn't supported ",color=Color.RED))
            raise Exception("Invalid feature argument.")
        
        inst_types = get_installation_types_for_feature(feature)
        if installation_type not in inst_types:
            logger.critical(color_msg(f"Installation type Chosen: {installation_type} isn't supported for feature: {feature}",color=Color.RED))
            raise Exception("Invalid installation type argument.")
        scripts.append(inst_types[installation_type])
        
    return scripts 

if __name__ == "__main__":
    builder()