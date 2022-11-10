from config_builder import ConfigBuilder, spinner
from typing import Any, Dict
from utils import DIR_PATH
import paramiko
import time
import sys
import os
from utils import color_msg, Color, logger, DIR_PATH, get_unique_file_name

INST_FILES = {"Ubuntu":"install_cuda_ubuntu.sh"}

class CudaInstall(ConfigBuilder):
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self) -> Dict[str, Any]:
        @spinner
        def _run_remote_script():
            install_log = get_unique_file_name("installation_log", DIR_PATH+os.sep+'logs')
            logger.info(color_msg(f"\nInstalling Cuda in newly created VSI.\n- See logs at {install_log}. Process might take a while.", color=Color.YELLOW))
            stdout = client.exec_command(f'chmod 777 {destination}/{file_to_execute}')[1] # returns the tuple (stdin,stdout,stderr)
            stdout = client.exec_command(f'{destination}/{file_to_execute}')[1]
            
            with open(install_log, "a") as f:
                for line in stdout:
                    f.write(line)

            # Blocking call
            exit_status = stdout.channel.recv_exit_status()          
            if exit_status == 0:
                logger.info(color_msg("Cuda installation script executed successfully.",color=Color.GREEN))
            else:
                logger.info(color_msg("Error executing script",color=Color.RED))

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
            sys.exit(1)

        # file_to_execute = 'test.sh'
        file_to_execute=INST_FILES[self.base_config['installation_type']]
        destination = "/tmp"

        # Connect to remote host
        key_obj = paramiko.RSAKey.from_private_key_file(self.base_config['auth']['ssh_private_key'])
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_to_ssh_port(key_obj)

        # Setup sftp connection and transmit script
        sftp = client.open_sftp()
        sftp.put(f'{DIR_PATH}/{file_to_execute}',f"{destination}/{file_to_execute}")
        sftp.close()
        _run_remote_script()

        client.close()

        return self.base_config

