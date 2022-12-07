from vpc_img_inst.config_builder import ConfigBuilder, spinner
from typing import Any, Dict
import paramiko
import time
import os
from vpc_img_inst.utils import color_msg, Color, logger, get_unique_file_name, DEFAULTS

class FeatureInstall(ConfigBuilder):
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.installation_scripts = self.base_config['scripts_path']
        self.inst_retries = DEFAULTS['script_inst_retries']

    def run(self) -> Dict[str, Any]:

        @spinner
        def _run_remote_script(script):
            feature = script[script.find('_')+1:script.rfind('_')]
            
            while self.inst_retries:  
                self.inst_retries -= 1          
                install_log = get_unique_file_name("installation_log", self.base_config['output_folder'])
                logger.info(color_msg(f"\nInstalling {feature} in newly created VSI.\n- See logs at {install_log}. Process might take a while.", color=Color.YELLOW))

                stdout = client.exec_command(f'chmod 777 {remote_destination}/{script_name}')[1] # returns the tuple (stdin,stdout,stderr)
                stdout = client.exec_command(f'{remote_destination}/{script_name}')[1]
                
                with open(install_log, "a") as f:
                    for line in stdout:
                        f.write(line)

                # Blocking call. returns when script completed/failed
                exit_status = stdout.channel.recv_exit_status()         
                if exit_status == 0:
                    logger.info(color_msg(f"""installation script "{script}" executed successfully.""",color=Color.LIGHTGREEN))
                    return True
                elif self.inst_retries:
                    time.sleep(2)
                    logger.error(color_msg(f"""Error executing "{script}". Retrying...""",color=Color.RED))

            raise Exception("Script installation failed. Terminating program.")

        @spinner
        def connect_to_ssh_port(key_obj):
            time.sleep(4)
            logger.info(f"user {self.base_config['auth']['ssh_user']} connecting to ssh port on host {self.base_config['node_config']['ip_address']} ")
            tries = 10
            msg = "Failed to connect to ssh port"
            while tries:
                try:
                    client.connect(self.base_config['node_config']['ip_address'], username=self.base_config['auth']['ssh_user'],pkey=key_obj)
                    return 
                except:
                    print(msg + ". Retrying..." if tries > 0 else msg)
                    tries -= 1
                    time.sleep(4)
            logger.critical(color_msg("\nFailed to connect to VSI via SSH. Terminating.\n", Color.RED))
            raise Exception("Failed to create to remote VM")

        for script in self.installation_scripts:

            file_to_execute_path = script
            script_name = file_to_execute_path.split(os.sep)[-1]
            remote_destination = "/tmp"

            # Connect to remote host
            key_obj = paramiko.RSAKey.from_private_key_file(self.base_config['auth']['ssh_private_key'])
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            connect_to_ssh_port(key_obj)

            # Setup sftp connection and transmit script
            sftp = client.open_sftp()
            sftp.put(f'{file_to_execute_path}',f"{remote_destination}/{script_name}")
            sftp.close()
            _run_remote_script(script)
            client.close()

        return self.base_config
