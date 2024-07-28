# SimpleConfigManager

SimpleConfigManager is a rudimentary configuration management tool designed to configure servers for the production service of a simple PHP web application. This tool abstracts file content and metadata management, Debian package installation and removal, and service management. It is idempotent and safe to apply configurations multiple times.

## Features

- **Bootstrap Dependencies:** If your tool has dependencies not available on a standard Ubuntu instance, include a `bootstrap.sh` program to resolve them.
- **File Management:** Provides an abstraction to specify a file's content and metadata (owner, group, mode).
- **Package Management:** Provides an abstraction to install and remove Debian packages.
- **Service Management:** Provides a mechanism for restarting a service when relevant files or packages are updated.
- **Idempotency:** Ensures safe application of configurations repeatedly.
- **Configuration Specification:** Configure a web server capable of running the provided PHP application.
- **Logging Support:**

## PHP Application

```php
<?php
    header("Content-Type: text/plain");
    echo "Hello, world!\n";
?>
```

## Installation
1. Clone the repository or extract the code from the tar file

2. Run the `bootstrap.sh` file

    The bootstrap.sh file updates the package list, installs Python and pip, and installs the required Python packages.

    ```./bootstrap.sh```

3. Set the Environment Variables

   Ensure that the environment variables SSH_USERNAME and SSH_PASSWORD are set with the SSH credentials.

    ```export SSH_USERNAME=root```

    ```export SSH_PASSWORD=<password>```

4. Edit Configuration Files

   Update the IP addresses in hosts.yaml to match your target hosts. Ensure your remote hosts are accessible via SSH and have the necessary permissions.

   Modify config.yaml to specify the configuration tasks you want to apply.

5. Run the Main Python File

   Execute the main script to apply the configurations to the specified hosts.

   ```python3 simpleconfigmanager.py```

## Logging
All actions and errors are logged to the `simpleconfigmanager.log` file. Check this file for detailed logs of the execution.

## Tool Architecture

- SimpleConfigManager Class: A utility class for managing configurations on remote hosts via SSH.
- Methods:
    - apply(host: str): Applies the configuration tasks to the specified host.

    - _is_service_installed(ssh: paramiko.SSHClient, service_name: str): Checks if a service is installed on the remote host.

    - _manage_file(ssh: paramiko.SSHClient, item: Dict[str, Any]): Manages a file on the remote host based on the configuration item.

    - _manage_package(ssh: paramiko.SSHClient, item: Dict[str, Any]): Manages a package on the remote host based on the configuration item.

    - _manage_service(ssh: paramiko.SSHClient, item: Dict[str, Any]): Manages a service on the remote host based on the configuration item.

## Further Improvements
1. Install and activate a python virtual environment in bootstrap script
2. Create unit tests for the code base
3. When apache2 is remove/deleted - ideally we should remove `/var/www` folder