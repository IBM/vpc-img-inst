from typing import Any, Dict
from vpc_img_inst.config_builder import ConfigBuilder, spinner
from vpc_img_inst.utils import color_msg, Color, logger, store_output, append_random_suffix
from vpc_img_inst.constants import DEFAULTS
import time


class ImageCreate(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.retries = DEFAULTS['image_create_retries']
        self.features = self.base_config['feature']

    def run(self) -> Dict[str, Any]:
        instance_volume_attachments = self.ibm_vpc_client.list_instance_volume_attachments(self.base_config['node_config']['vsi_id']).get_result()
        boot_volume_id = instance_volume_attachments['volume_attachments'][0]['volume']['id']
        default_image_name = ''
        for feature in self.features:
            default_image_name += feature+'-'
        default_image_name += f"""{self.base_config['node_config']['image_name']}"""  
        image_name = append_random_suffix(base_name=default_image_name)
        
        logger.info("Stopping VM instance...")
        self.ibm_vpc_client.create_instance_action(self.base_config['node_config']['vsi_id'], "stop")
        # blocks until instance stopped.
        self.poll_instance_status(self.base_config['node_config']['vsi_id']) 
        
        if self.retries:
            self.retries -= 1
            self.create_image(image_name, self.base_config['node_config']['resource_group_id'], boot_volume_id)
            return self.base_config
    
    
    def create_image(self, image_name, resource_group_id, boot_volume_id):
        payload = {"name": image_name,
                    "resource_group":{"id":resource_group_id},
                    "source_volume": {"id": boot_volume_id}}    
        image_data = self.ibm_vpc_client.create_image(payload).result
        logger.info(color_msg(f"""Creating image: "{image_name}" with id: "{image_data['id']}". Process may take a while. """, Color.YELLOW))
  
        self.base_config['new_image_id'] = image_data['id']
        # blocking call that forces the program to wait for the creation of the image.  
        response = self.poll_image_status(image_data['id'],image_name)

    @spinner
    def poll_image_status(self,image_id, image_name):
        tries = 300 # waits up to 50 min with 10 sec intervals
        sleep_interval = 10
        msg = ""
        while tries:
            image_status = self.ibm_vpc_client.get_image(image_id).result['status']
            if image_status == 'available':
                logger.info(color_msg(f"""\nImage named: "{image_name}" with id: "{image_id}" was created successfully.\n""", Color.LIGHTGREEN))
                store_output({"new_image":{'image_id':image_id, 'image_name':image_name}},self.base_config)
                return True
            elif image_status in ['failed','unusable','deprecated','deleting']:
                logger.info(color_msg(f"failed to create image {image_id}. Retrying...", Color.RED))
                store_output({f"failed_image-{DEFAULTS['image_create_retries']-self.retries}":{'image_id':image_id, 'image_name':image_name}},self.base_config)
                time.sleep(10)
                self.run()  # retry
                return True
            else:
                tries -= 1
                time.sleep(sleep_interval)
        logger.critical(color_msg(f"Failed to create image {image_id} within the expected time frame of {tries*sleep_interval/60} minutes.\n", Color.RED))
        return False

    @spinner
    def poll_instance_status(self, instance_id):
        tries = 30 # waits up to 1 min with 2 sec intervals
        sleep_interval = 2
        msg = ""
        while tries:
            instance_status = self.ibm_vpc_client.get_instance(instance_id).result['status']
            if instance_status == 'stopped':
                return True
            elif instance_status in ['failed']:
                logger.info(color_msg("\nInstance failed to stop.\n",color=Color.RED))
                return False
            else:
                tries -= 1
                time.sleep(sleep_interval)
        logger.critical(color_msg(f"\nInstance failed to stop within expected time frame of {tries*sleep_interval/60} minutes.\n",color=Color.RED))
        return False
