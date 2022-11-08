from typing import Any, Dict
from config_builder import ConfigBuilder, spinner
from utils import color_msg, Color, logger
import time


class ImageCreate(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self) -> Dict[str, Any]:
        instance_volume_attachments = self.ibm_vpc_client.list_instance_volume_attachments(self.base_config['node_config']['vsi_id']).get_result()
        boot_volume_id = instance_volume_attachments['volume_attachments'][0]['volume']['id']

        images = self.ibm_vpc_client.list_images().get_result()
        image_names = [image['name'] for image in images['images']]
        image_name = default_image_name = "cuda"+self.base_config['node_config']['image_name'] 

        c = 1
        while default_image_name in image_names:    # find next available vsi name
            default_image_name = f'{image_name}-{c}'
            c += 1

        self.ibm_vpc_client.create_instance_action(self.base_config['node_config']['vsi_id'], "stop")
        # blocks until instance stopped.
        self.poll_instance_status(self.base_config['node_config']['vsi_id']) 
        logger.debug("Stopping instance.")
             
        self.create_image(image_name, self.base_config['node_config']['resource_group_id'], boot_volume_id)
        return self.base_config
    
    
    def create_image(self, image_name, resource_group_id, boot_volume_id):
        payload = {"name": image_name,
                    "resource_group":{"id":resource_group_id},
                    "source_volume": {"id": boot_volume_id}}    
        image_data = self.ibm_vpc_client.create_image(payload).result
        print(color_msg(f"""Creating image: "{image_name}" with id: "{image_data['id']}". Process may take a while, visit the UI to track its progress. """, Color.LIGHTGREEN))
  
        self.base_config['new_image_id'] = image_data['id']
        response = self.poll_image_status(image_data['id'],image_name)

    @spinner
    def poll_image_status(self,image_id, image_name):
        tries = 300 # waits up to 50 min with 10 sec interval
        sleep_interval = 10
        msg = ""
        while tries:
            image_status = self.ibm_vpc_client.get_image(image_id).result['status']
            if image_status == 'available':
                print(color_msg(f"""\nImage named: "{image_name}" with id: "{image_id}" was created successfully .\n""", Color.LIGHTGREEN))
                return True
            elif image_status in ['failed','unusable','deprecated','deleting']:
                print(color_msg(f"failed to create image {image_id}.", Color.RED))
                return False
            else:
                # print(msg + ". Retrying..." if tries > 0 else msg)
                tries -= 1
                time.sleep(sleep_interval)
        print(color_msg(f"Failed to create image {image_id} within the expected time frame of {tries*sleep_interval/60} minutes.\n", Color.RED))
        return False

    @spinner
    def poll_instance_status(self, instance_id):
        tries = 30 # waits up to 1 min with 2 sec interval
        sleep_interval = 2
        msg = ""
        while tries:
            instance_status = self.ibm_vpc_client.get_instance(instance_id).result['status']
            if instance_status == 'stopped':
                return True
            elif instance_status in ['failed']:
                print(color_msg("\nInstance failed to stop.\n",color=Color.RED))
                return False
            else:
                # print("Retrying...")
                tries -= 1
                time.sleep(sleep_interval)
        print(color_msg(f"\nInstance failed to stop within expected time frame of {tries*sleep_interval/60} minutes.\n",color=Color.LIGHTGREEN))
        return False
