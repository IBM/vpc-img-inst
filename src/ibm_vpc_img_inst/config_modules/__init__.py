from ibm_vpc_img_inst.config_modules.apikey_config import ApiKeyConfig
from ibm_vpc_img_inst.config_modules.endpoint_config import EndpointConfig
from ibm_vpc_img_inst.config_modules.ip_config import FloatingIpConfig
from ibm_vpc_img_inst.config_modules.ssh_config import SshKeyConfig
from ibm_vpc_img_inst.config_modules.vpc_config import VPCConfig
from ibm_vpc_img_inst.config_modules.vsi_config import VSIConfig
from ibm_vpc_img_inst.config_modules.image_config import ImageConfig
from ibm_vpc_img_inst.config_modules.install_feature import FeatureInstall
from ibm_vpc_img_inst.config_modules.image_create import ImageCreate
from ibm_vpc_img_inst.config_modules.delete_resources import DeleteResources


MODULES = [ApiKeyConfig, EndpointConfig, VPCConfig, ImageConfig,
            SshKeyConfig, VSIConfig, FloatingIpConfig, FeatureInstall, ImageCreate, DeleteResources]