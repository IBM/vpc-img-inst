from vpc_img_inst.config_modules.apikey_config import ApiKeyConfig
from vpc_img_inst.config_modules.endpoint_config import EndpointConfig
from vpc_img_inst.config_modules.ip_config import FloatingIpConfig
from vpc_img_inst.config_modules.ssh_config import SshKeyConfig
from vpc_img_inst.config_modules.vpc_config import VPCConfig
from vpc_img_inst.config_modules.vsi_config import VSIConfig
from vpc_img_inst.config_modules.image_config import ImageConfig
from vpc_img_inst.config_modules.install_feature import FeatureInstall
from vpc_img_inst.config_modules.image_create import ImageCreate
from vpc_img_inst.config_modules.delete_resources import DeleteResources


MODULES = [ApiKeyConfig, EndpointConfig, VPCConfig, ImageConfig,
            SshKeyConfig, VSIConfig, FloatingIpConfig, FeatureInstall, ImageCreate, DeleteResources]