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
ibm-vpc-img-inst [--iam-api-key IAM_API_KEY] [--region REGION] [-i INPUT_FILE] [-o OUTPUT_FOLDER] [-im BASE_IMAGE_NAME] [-it INSTALLATION_TYPE] [--compute-iam-endpoint IAM_ENDPOINT] [-y] [--version] 
```

Get a short description of the available flags via ```ibm-vpc-img-inst --help```

<br/>

#### Flags Detailed Description

<!--- <img width=125/> is used in the following table to create spacing --->
 |<span style="color:orange">Key|<span style="color:orange">Default|<span style="color:orange">Mandatory|<span style="color:orange">Additional info|
 |---|---|---|---|
 | iam-api-key   | |yes|IBM Cloud API key. To generate a new API Key adhere to the following [guide](https://www.ibm.com/docs/en/spectrumvirtualizecl/8.1.3?topic=installing-creating-api-key)
 | input-file    |<project_root_folder>/defaults.py| no | Existing config file to be used as a template in the configuration process |
 | output-folder   |<project_root_folder>/logs/ | no |Path to folder storing IDs of resources created by this program and installation logs |
 | version       | | no |Returns ibm-ray-config's package version|
 |region| us-south| no|Geographical location for deployment and scope for available resources by the IBM-VPC service. Regions are listed <a href="https://cloud.ibm.com/docs/vpc?topic=vpc-creating-a-vpc-in-a-different-region&interface=cli"> here</a>. |
 |base-image-name| ibm-ubuntu-20-04-4-minimal-amd64-2| no| Prefix of an image name from your account, on which the produced image will be based. Could be either an IBM stock image as explained [here](https://cloud.ibm.com/docs/vpc?topic=vpc-about-images) or a custom image.|
  | installation-type| Ubuntu | no |Type of CUDA installation to use, e.g. Ubuntu, Fedora, RHEL.|
 compute_iam_endpoint|https://iam.cloud.ibm.com|no|Alternative IAM endpoint url for the cloud provider, e.g. https://iam.test.cloud.ibm.com|

