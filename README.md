# Image Installer For IBM-VPC

ibm-vpc-img-inst is a CLI tool that greatly simplifies user experience by generating images with out of the box tools installed.  
Currently supported tools: CUDA.

## Setup

Mostly tested with Fedora 35 and Ubuntu 20, but should work with most Linux systems.   
#### Requirements
- `ssh-keygen` utility installed:
    ```
    sudo apt install openssh-client
    ```
- Install the package **locally** using pip:  
    run `pip install .` from the project's root directory.  
    This requirement is temporary until this program will get clearance and be published in PyPi.
## Usage
Use the configuration tool as follows:

```
ibm-vpc-img-inst [--iam-api-key IAM_API_KEY] [--region REGION] [-i INPUT_FILE] [-o OUTPUT_FOLDER] [-f FEATURE] [-im BASE_IMAGE_NAME] [-it INSTALLATION_TYPE] [--compute-iam-endpoint IAM_ENDPOINT] [-y] [--version] 
```
### Examples
- `ibm-vpc-img-inst -a <API_KEY> -y -f cuda -it rhel -im ibm-redhat-8-6`
- `ibm-vpc-img-inst -a <API_KEY> -y -f docker -it ubuntu` (using default base image)

Get a short description of the available flags via ```ibm-vpc-img-inst --help```

### Flags Detailed Description
Note - Flags' values are case sensitive.  
For example `--feature cuda` also represents the folder's name, ergo the program will fail to detect the feature using `--feature CUDA`.     

<!--- <img width=125/> is used in the following table to create spacing --->
 |<span style="color:orange">Key|<span style="color:orange">Default|<span style="color:orange">Mandatory|<span style="color:orange">Additional info|
 |---|---|---|---|
 | iam-api-key   | |yes|IBM Cloud API key. To generate a new API Key adhere to the following [guide](https://www.ibm.com/docs/en/spectrumvirtualizecl/8.1.3?topic=installing-creating-api-key)
 | input-file    |<project_root_folder>/defaults.py| no | Existing config file to be used as a template in the configuration process |
 | output-folder   |<project_root_folder>/logs/ | no |Path to folder storing IDs of resources created by this program and installation logs |
 | version       | | no |Returns ibm-vpc-img-inst's package version|
 |region| us-south| no|Geographical location for deployment and scope for available resources by the IBM-VPC service. Regions are listed <a href="https://cloud.ibm.com/docs/vpc?topic=vpc-creating-a-vpc-in-a-different-region&interface=cli"> here</a>. |
 |base-image-name| ibm-ubuntu-20-04-4-minimal-amd64-2| no| Prefix of an image name from your account, on which the produced image will be based. Could be either an IBM stock image as explained [here](https://cloud.ibm.com/docs/vpc?topic=vpc-about-images) or a custom image.|
  | installation-type| Ubuntu | no |type of installation to use, e.g. for feature cuda the currently supported types are: Ubuntu and RHEL.|
  | feature| cuda | no |Feature to install on the produced image. Currently supporting: cuda and docker.|
  | cleanup| no | no |Path to a resources file, that will be submitted for deletion. Program will be terminated subsequently.|
 compute_iam_endpoint|https://iam.cloud.ibm.com|no|Alternative IAM endpoint url for the cloud provider, e.g. https://iam.test.cloud.ibm.com|


## Extendability & Contribution
To extend the features/installation types this program support, please follow the next steps:
1. Create a folder named after the feature in camel case format, e.g nodeJS
2. Create installation type scripts for the feature and name them in the following format: `install_<FeatureName>_<installation_type>.sh`, e.g. "install_cuda_ubuntu.sh".
3. Store the scripts in their respective feature folder.
4. To extend the tool for your own personal use, place the feature folder in `~/.ibm-vpc-img-inst`.  
To contribute a new feature place its folder under the project's `src/ibm_vpc_img_inst/installation_scripts`.  



## Clean-up
All resources created during the execution of the program will be automatically removed and unregistered from the IBM-VPC (apart from the created image). This process also takes place upon a failed run. 
#### Manual clean-up
To manually remove byproduct resources run: `ibm-vpc-img-inst -c <path_to_resources_file>`.  
Users may have to resort to running this command in the odd occasion where this program fails to remove its byproducts.   
The default path to the resources file is located in the `logs` folder.  
