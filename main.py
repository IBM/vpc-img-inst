import importlib
import pkg_resources
import os
import click
import yaml
import config_modules
from utils import color_msg, Color, verify_paths

import click
@click.command()
@click.option('--output-file', '-o', help='Output filename to save configurations')
@click.option('--input-file', '-i', help=f'Template for the new configuration')
@click.option('--iam-api-key', '-a', help='IAM_API_KEY')
@click.option('--version', '-v', help=f'Get package version', is_flag=True)
@click.option('--endpoint', help='IBM Cloud API endpoint')
@click.option('--compute-iam-endpoint', help='IAM endpoint url used for compute instead of default https://iam.cloud.ibm.com')
def builder(iam_api_key, output_file, input_file, version, endpoint, compute_iam_endpoint):
    iam_api_key =os.environ["RESEARCH"]
    if version:
        print(f"{pkg_resources.get_distribution('ibm-ray-config').project_name} "
              f"{pkg_resources.get_distribution('ibm-ray-config').version}")
        exit(0)

    print(color_msg("\nWelcome to ...\n", color=Color.YELLOW))


    # if input_file is empty, path to defaults.py is returned.
    input_file, output_file = verify_paths(input_file, output_file)

    
    with open(input_file) as f:
        base_config = yaml.safe_load(f)
    base_config, modules = validate_api_keys(base_config, iam_api_key,compute_iam_endpoint)

    if endpoint:
        base_config['endpoint'] = endpoint

    for module in modules:
        next_module = module(base_config)
        base_config = next_module.run()

    with open(output_file, 'w') as outfile:
        yaml.dump(base_config, outfile, default_flow_style=False)

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