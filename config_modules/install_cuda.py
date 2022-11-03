from config_builder import ConfigBuilder, spinner
from typing import Any, Dict
from subprocess import Popen, PIPE
from utils import DIR_PATH
import paramiko

from utils import free_dialog, get_option_from_list

class CudaInstall(ConfigBuilder):
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self) -> Dict[str, Any]:

        @spinner
        def _run_remote_script():
            stdout = client.exec_command(f'chmod 777 {destination}/{file_to_execute}')[1] # returns the tuple (stdin,stdout,stderr)
            stdout = client.exec_command(f'{destination}/{file_to_execute}')[1]
            for line in stdout:
                print(line)
            # with open("installation_log.txt", "a") as f:
            #     f.write(stdout)
        
        # file_to_execute = 'test.sh'
        file_to_execute = 'install_cuda.sh'
        destination = "/tmp"

        # Connect to remote host
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.base_config['node_config']['ip'], username=self.base_config['auth']['ssh_user'])

        # Setup sftp connection and transmit script
        sftp = client.open_sftp()
        sftp.put(f'{DIR_PATH}/{file_to_execute}',f"{destination}/{file_to_execute}")
        sftp.close()
        _run_remote_script()

        client.close()

        return self.base_config

