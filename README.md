# Image Installer For IBM-VPC

ibm-vpc-img-inst is a CLI tool that automates generation of custom VSI images by installing _features_ (software bundles) on base images


## Setup

Mostly tested with Fedora 35 and Ubuntu 20, but should work with most Linux and Mac systems.   
#### Requirements
- `ssh-keygen` utility - available as part of the Open SSH client.

#### Installation
- `pip install ibm-vpc-img-inst`
## Usage
- Create a new custom image:
```
ibm-vpc-img-inst [--iam-api-key IAM_API_KEY] [--region REGION] [-i INPUT_FILE] [-o OUTPUT_FOLDER] [-f FEATURE] [-im BASE_IMAGE_NAME] [-it INSTALLATION_TYPE] [--compute-iam-endpoint IAM_ENDPOINT] [-y] 
[--cleanup PATH_TO_RESOURCES_FILE][--version] [--help]
```
```ibm-vpc-img-inst --help```
### Examples
- `ibm-vpc-img-inst -a <API_KEY> -y -f cuda -it rhel -im ibm-redhat-8-6`  
Create a custom image of CUDA on RHEL 8.6
- `ibm-vpc-img-inst -a <API_KEY> -y -f docker -it ubuntu` (using default base image)  
Create a custom image of Docker on Ubuntu (default 20.4) 
- `ibm-vpc-img-inst --help`  
Get a short description of the available flags via  
- `ibm-vpc-img-inst -c <PATH_TO_FILE>`  
Clean-up a previously failed execution (see [Cleanup](##-Clean-up))

### Flags Detailed Description
Note - Flag values are case sensitive.  
For example `--feature cuda` !=  `--feature CUDA`.

<!--- <img width=125/> is used in the following table to create spacing --->
 |<span style="color:orange">Key|<span style="color:orange">Default|<span style="color:orange">Mandatory|<span style="color:orange">Additional info|
 |---|---|---|---|
 | iam-api-key   | NA|yes|IBM Cloud API key. To generate a new API Key adhere to the following [guide](https://www.ibm.com/docs/en/spectrumvirtualizecl/8.1.3?topic=installing-creating-api-key)
 | input-file    |<project_root_folder>/defaults.py| no | Existing config file to be used as a template in the configuration process |
 | output-folder   |<project_root_folder>/logs/ | no |Path to folder storing IDs of resources created by this program and installation logs |
 | version       | NA| no |Returns ibm-vpc-img-inst's package version|
 |region| us-south| no|Geographical location for deployment and scope for available resources by the IBM-VPC service. Regions are listed <a href="https://cloud.ibm.com/docs/vpc?topic=vpc-creating-a-vpc-in-a-different-region&interface=cli"> here</a>. |
 |base-image-name| ibm-ubuntu-20-04-4-minimal-amd64-2| no| Prefix of an image name from your account, on which the produced image will be based. Could be either an IBM stock image as explained [here](https://cloud.ibm.com/docs/vpc?topic=vpc-about-images) or a custom image.|
  | installation-type| ubuntu | no |type of installation to use, e.g. for feature cuda the currently supported types are: ubuntu and rhel.|
  | feature| cuda | no |Feature to install on the produced image. Currently supporting: cuda and docker.|
  | cleanup| NA | no |Path to a resources file, that will be submitted for deletion. Program will be terminated subsequently.|
 compute_iam_endpoint|https://iam.cloud.ibm.com|no|Alternative IAM endpoint url for the cloud provider, e.g. https://iam.test.cloud.ibm.com|


## Extendability
To extend the features/installation types this program support, please follow the next steps:
1. To add a new feature, inside `~/.ibm-vpc-img-inst`, create a folder named after the feature in camel case format, e.g nodeJS.
2. to add new installation type, inside a feature's folder add a new installation type by adding a script with the following naming format: `install_<FeatureName>_<installation_type>.sh`, e.g. "install_cuda_ubuntu.sh".


## Clean-up
All resources created during the execution of the program will be automatically removed and unregistered from the IBM-VPC (apart from the created image). This process also takes place upon a failed run. 
#### Manual clean-up
To manually remove byproduct resources run: `ibm-vpc-img-inst -c <path_to_resources_file>`.  
Users may have to resort to running this command in the odd occasion where this program fails to remove its byproducts.   
The default path to the resources file is located in the `logs` folder.  
