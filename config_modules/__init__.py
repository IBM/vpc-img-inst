from config_modules.apikey_config import ApiKeyConfig
from config_modules.endpoint_config import EndpointConfig
from config_modules.ip_config import FloatingIpConfig
from config_modules.ssh_config import SshKeyConfig
from config_modules.vpc_config import VPCConfig
from config_modules.vsi_config import VSIConfig
from config_modules.image_config import ImageConfig
from config_modules.install_cuda import CudaInstall
from config_modules.gpu_image import GPUImage
from config_modules.delete_resources import DeleteResources


MODULES = [ApiKeyConfig, EndpointConfig, VPCConfig, ImageConfig,
            SshKeyConfig, VSIConfig, FloatingIpConfig, CudaInstall, GPUImage, DeleteResources]
