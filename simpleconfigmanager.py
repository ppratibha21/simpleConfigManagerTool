import yaml
import os
import paramiko
import logging
from typing import Dict, Any

class SimpleConfigManager:
    '''
    SimpleConfigManager is a utility class for managing configurations on remote hosts via SSH.

    This class reads configuration from a YAML file and applies various configuration tasks such as
    managing files, packages, and services on a remote host. It uses SSH for remote communication
    and supports logging to a file.

    Attributes:
        config (dict): The configuration loaded from the YAML file.
        logger (logging.Logger): The logger instance for logging messages.

    Methods:
        apply(host: str) -> None:
            Applies the configuration tasks to the specified host.
        _is_service_installed(ssh: paramiko.SSHClient, service_name: str) -> bool:
            Checks if a service is installed on the remote host.
        _manage_file(ssh: paramiko.SSHClient, item: Dict[str, Any]) -> None:
            Manages a file on the remote host based on the configuration item.
        _manage_package(ssh: paramiko.SSHClient, item: Dict[str, Any]) -> None:
            Manages a package on the remote host based on the configuration item.
        _manage_service(ssh: paramiko.SSHClient, item: Dict[str, Any]) -> None:
            Manages a service on the remote host based on the configuration item.
    '''
    def __init__(self, config_file: str):
        # Load configuration from the specified YAML file
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        # Configure logging to write to a file with a specific format
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='simpleconfigmanager.log', filemode='w')
        self.logger = logging.getLogger(__name__)

    def apply(self, host: str) -> None:
        # Retrieve SSH credentials from environment variables
        username = os.getenv('SSH_USERNAME')
        password = os.getenv('SSH_PASSWORD')

        # Check if SSH credentials are set
        if not username or not password:
            self.logger.error("SSH_USERNAME and SSH_PASSWORD environment variables must be set")
            return

        # Initialize SSH client and set policy to accept unknown host keys
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            # Connect to the host using SSH
            ssh.connect(host, username=username, password=password)
            self.logger.info(f"Connected to {host}")
        except paramiko.SSHException as e:
            self.logger.error(f"SSH connection failed: {e}")
            return

        # Process each item in the configuration sequentially
        for item in self.config:
            self.logger.debug(f"Processing item: {item}")
            try:
                if item['type'] == 'file':
                    self._manage_file(ssh, item)
                elif item['type'] == 'package':
                    state = item.get('state')
                    if state not in ['present', 'absent']:
                        self.logger.error(f"Invalid state '{state}' for package '{item['name']}'. Must be 'present' or 'absent'.")
                        return
                    self._manage_package(ssh, item)
                elif item['type'] == 'service':
                    state = item.get('state')
                    if state not in ['start', 'stop', 'reload', 'restart']:
                        self.logger.error(f"Invalid state '{state}' for service '{item['name']}'. Must be 'start', 'stop', 'reload', or 'restart'.")
                        return
                    if self._is_service_installed(ssh, item['name']):
                        self._manage_service(ssh, item)
                    else:
                        self.logger.error(f"Service '{item['name']}' is not installed. Cannot perform any action on it")
                        return
            except Exception as e:
                self.logger.error(f"Failed to manage {item['type']}: {e}")

        # Close the SSH connection
        ssh.close()
        self.logger.info("SSH connection closed")

    def _is_service_installed(self, ssh: paramiko.SSHClient, service_name: str) -> bool:
        # Check if the service is installed by querying the package manager
        try:
            stdin, stdout, stderr = ssh.exec_command(f"dpkg -l | awk '$2 == \"{service_name}\"'")
            return_code = stdout.channel.recv_exit_status()

            if return_code == 0:
                output = stdout.read().decode().strip()
                if output:
                    return True
                else:
                    return False
            else:
                error_message = stderr.read().decode().strip()
                return False
        except Exception as e:
            self.logger.error(f"An error occurred while checking service installation: {e}")
            return False

    def _manage_file(self, ssh: paramiko.SSHClient, item: Dict[str, Any]) -> None:
        # Open an SFTP session
        content = item['content']
        path = item['path']
        owner = item.get('owner', 'www-data')
        group = item.get('group', 'www-data')
        mode = item.get('mode', '0644')

        sftp = ssh.open_sftp()

        try:
            # Write content to the target file
            with sftp.file(path, 'w') as f:
                f.write(content)
            self.logger.debug(f"Wrote content directly to file: {path}")

            # Set ownership and permissions
            ssh.exec_command(f"chown {owner}:{group} {path}")
            ssh.exec_command(f"chmod {mode} {path}")
            self.logger.info(f"Set ownership and permissions for {path}")

            # Remove index.html if it exists(we don't need it)
            index_html_path = "/var/www/html/index.html"
            stdin, stdout, stderr = ssh.exec_command(f"rm -f {index_html_path}")
            stdout.channel.recv_exit_status()  # Wait for the command to complete
            self.logger.info(f"Removed {index_html_path} if it existed")
        except IOError as e:
            self.logger.error(f"Failed to manage file: {e}")
        finally:
            # Close the SFTP session
            sftp.close()
            self.logger.debug("SFTP connection closed")


    def _manage_package(self, ssh: paramiko.SSHClient, item: Dict[str, Any]) -> None:
        name = item['name']
        state = item.get('state')

        self.logger.info(f"Managing package: {name}, state: {state}")
        if state == 'present':
            # Install the package
            stdin, stdout, stderr = ssh.exec_command(f"apt-get install -y {name}")
        elif state == 'absent':
            # Remove the package
            stdin, stdout, stderr = ssh.exec_command(f"apt-get purge -y {name} && apt-get autoremove -y")
        else:
            self.logger.error(f"Unknown state '{state}' for package: {name}")

        # Log the output and errors
        out = stdout.read().decode()
        err = stderr.read().decode()
        self.logger.info(out)
        if err:
            self.logger.error(f"Error installing {name}: {err}")


    def _manage_service(self, ssh: paramiko.SSHClient, item: Dict[str, Any]) -> None:
        name = item['name']
        state = item.get('state')
        self.logger.info(f"Managing service: {name}, state: {state}")

        try:
            # Manage the service based on the desired state
            if state == 'start':
                ssh.exec_command(f"systemctl start {name}")
                self.logger.info(f"Started service: {name}")
            elif state == 'stop':
                ssh.exec_command(f"systemctl stop {name}")
                self.logger.info(f"Stopped service: {name}")
            elif state == 'restart':
                ssh.exec_command(f"systemctl restart {name}")
                self.logger.info(f"Restarted service: {name}")
            elif state == 'reload':
                ssh.exec_command(f"systemctl reload {name}")
                self.logger.info(f"Reloaded service: {name}")
            else:
                self.logger.error(f"Unknown state '{state}' for service: {name}")
                return
        except Exception as e:
            self.logger.error(f"Failed to manage service {name}: {e}")

if __name__ == "__main__":
    '''
    Main entry point for the SimpleConfigManager tool.

    This script initializes the SimpleConfigManager with a configuration file,
    loads the inventory of hosts from 'hosts.yaml', and applies the configuration
    to each server listed in the inventory.

    Workflow:
    1. Initialize the SimpleConfigManager with 'config.yaml'.
    2. Load the inventory of hosts from 'hosts.yaml'.
    3. Iterate over each server in the inventory and apply the configuration.

    Exception Handling:
    - Logs an error message if any exception occurs during the process.

    Notes:
    - The configuration file 'config.yaml' should be present in the same directory.
    - The inventory file 'hosts.yaml' should contain a list of servers under the 'servers' key.
    '''
    try:
        config = SimpleConfigManager('config.yaml')
        with open('hosts.yaml', 'r') as f:
            inventory = yaml.safe_load(f)
        for server in inventory['servers']:
            config.apply(server['host'])

    except Exception as e:
        config.logger.error(f"An error occurred: {str(e)}")
