
from setuptools import setup, find_packages
from setuptools.command.install import install
import os 
import shutil
from pathlib import Path
PACKAGE_NAME = 'vpc-img-inst'
INSTALLATION_DIR_NAME = 'installation_scripts'
USER_SCRIPTS_FOLDER = str(Path.home())+os.sep+f".{PACKAGE_NAME}" 
PROJECT_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)),'src','vpc_img_inst')

class CustomInstallCommand(install):
    """
    This class inherits from setuptools' install class to create the users scripts folder
    post installation ((pip) install) and copy the project's scripts to said folder. 
    """
    
    def run(self):
        install.run(self)
        
        if not os.path.exists(USER_SCRIPTS_FOLDER):
            print(f'Copying project scripts to {USER_SCRIPTS_FOLDER}')
            src = os.path.join(PROJECT_ROOT,INSTALLATION_DIR_NAME)
            dest = USER_SCRIPTS_FOLDER
            shutil.copytree(src, dest)



def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

find_packages(where='src',exclude=['logs'])

setup(
    name='vpc-img-inst',
    version='1.0.0b3',
    author =' Omer J Cohen',
    author_email = 'cohen.j.omer@gmail.com',
    description = 'vpc-img-inst is a lightweight script for quick-and-dirty generation of custom VSI images by installing features (software bundles) on base images.',
    long_description=read('README.md'),
    long_description_content_type = "text/markdown",
    url = 'https://github.com/IBM-Cloud/vpc-img-inst',
    install_requires=[
        'click==8.0.4',
        'ibm_cloud_sdk_core==3.16.0',
        'ibm_platform_services==0.27.0',
        'ibm_vpc==0.12.0',
        'ibm_watson==6.1.0',
        'inquirer==2.10.1',
        'paramiko==2.11.0',
        'PyYAML==6.0',
        'setuptools==63.2.0'
    ],

    # Creates script named vpc-img-inst under ~/<python_folder>/bin/vpc-img-inst.
    # it is asked to pass parameters to builder() of vpc_img_inst.main. 
    entry_points={
    'console_scripts': ['vpc-img-inst=vpc_img_inst:main.builder']
    },
    # include otherwise undetected installation scripts and defaults.yaml  
    package_data={'': ['*.sh','*.yaml']},
    # inform setuptools to modify standard installation class. in this instance: setuptools.command.install 
    cmdclass={'install': CustomInstallCommand},
    python_requires = ">=3.6",
)

