import pkg_resources
import os
import sys
import click
import yaml
import config_modules
from utils import color_msg, Color, verify_paths, get_confirmation, store_output
# default values for the vsi on which the produced image will base upon  
DEFAULTS = {'image_name':'ibm-ubuntu-20-04-4-minimal-amd64-2', 'region':'us_south'}

import click
@click.command()
@click.option('--output-file', '-o', help='Output filename to save configurations')
@click.option('--input-file', '-i', help=f'Template for the new configuration')
@click.option('--iam-api-key', '-a', help='IAM_API_KEY')
@click.option('--version', '-v', help=f'Get package version', is_flag=True)
@click.option('--region', help='IBM Cloud region, e.g: us-south, us-east, eu-de, eu-gb')
@click.option('--auto','-y',is_flag=True, help='Skips confirmation requests')
@click.option('--compute-iam-endpoint', help='IAM endpoint url used for compute instead of default https://iam.cloud.ibm.com')
def builder(iam_api_key, output_file, input_file, version, region, auto, compute_iam_endpoint):

    print(color_msg("DEBUGGING - API KEY HARDCODED", color=Color.RED))
    iam_api_key = os.environ["RESEARCH"]

    # print(color_msg("DEBUGGING - Source file is TEST.yaml", color=Color.RED))
    test = False # affecting verify_paths()

    if version:
        print(f"{pkg_resources.get_distribution('').project_name} "
              f"{pkg_resources.get_distribution('').version}")
        exit(0)

    print(color_msg("\nWelcome to IBM VPC Image CUDA Installer\n", color=Color.YELLOW))


    # if input_file is empty, path to defaults.py is returned.
    input_file, output_file = verify_paths(input_file, output_file, test=test)
    
    with open(input_file) as f:
        base_config = yaml.safe_load(f)
    
    base_config['output_file'] = output_file

    base_config, modules = validate_api_keys(base_config, iam_api_key, compute_iam_endpoint)
    base_config['auto'] = auto

    base_config['region'] = region if region else 'us-south'
    if not auto:
        confirmation = get_confirmation(f"Creating image in region: {region}?")['answer']
        if not confirmation:
            sys.exit(0)

    for module in modules:
        next_module = module(base_config)
        base_config = next_module.run()
    
    print(color_msg("\nProgram Concluded. Inspect outputs for details.\n", color=Color.YELLOW))

def validate_api_keys(base_config, iam_api_key, compute_iam_endpoint):
    """validates the api key specified.
    returns a base config dict, updated with the api-key field populated and the post api-key module removal modules list  """
    # The API_KEY module is invoked and popped from the list. 
    modules = config_modules.MODULES
    api_key_module = modules[0]
    base_config = api_key_module(base_config).run(api_key=iam_api_key,
                                                  compute_iam_endpoint=compute_iam_endpoint)

    modules = modules[1:]
    return base_config , modules


if __name__ == "__main__":
    builder()