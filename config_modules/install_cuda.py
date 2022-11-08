from config_builder import ConfigBuilder, spinner
from typing import Any, Dict
from utils import DIR_PATH
import paramiko
import time
from utils import color_msg, Color, logger, DIR_PATH, get_unique_file_name


class CudaInstall(ConfigBuilder):
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self) -> Dict[str, Any]:
        @spinner
        def _run_remote_script():
            install_log = get_unique_file_name("installation_log", DIR_PATH)
            print(color_msg(f"\nInstalling Cuda in newly created VSI.\n- See logs at {install_log}. Process might take a while.", color=Color.YELLOW))
            stdout = client.exec_command(f'chmod 777 {destination}/{file_to_execute}')[1] # returns the tuple (stdin,stdout,stderr)
            stdout = client.exec_command(f'{destination}/{file_to_execute}')[1]
            
            with open(install_log, "a") as f:
                for line in stdout:
                    f.write(line)

            # Blocking call
            exit_status = stdout.channel.recv_exit_status()          
            if exit_status == 0:
                print(color_msg("Cuda installation script executed successfully.",color=Color.GREEN))
            else:
                print(color_msg("Error executing script",color=Color.RED))

        @spinner
        def connect_to_ssh_port():
            logger.info("connecting to ssh port")
            tries = 10
            msg = "Failed to connect to ssh port"
            while tries:
                try:
                    client.connect(self.base_config['node_config']['ip'], username=self.base_config['auth']['ssh_user'])
                    return 
                except:
                    print(msg + ". Retrying..." if tries > 0 else msg)
                    tries -= 1
                    time.sleep(4)
            print(color_msg("\nFailed to connect to VSI via SSH. Terminating.\n", Color.RED))
            raise
        
        # file_to_execute = 'test.sh'
        file_to_execute = 'install_cuda_ubuntu.sh'
        destination = "/tmp"

        # Connect to remote host
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_to_ssh_port()

        # Setup sftp connection and transmit script
        sftp = client.open_sftp()
        sftp.put(f'{DIR_PATH}/{file_to_execute}',f"{destination}/{file_to_execute}")
        sftp.close()
        _run_remote_script()

        client.close()

        return self.base_config

