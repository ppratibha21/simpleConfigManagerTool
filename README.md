# SimpleConfigManager

SimpleConfigManager is a rudimentary configuration management tool designed to configure servers for the production service of a simple PHP web application. This tool abstracts file content and metadata management, Debian package installation and removal, and service management. It is idempotent and safe to apply configurations multiple times.

## Features

- **Bootstrap Dependencies:** Includes a `bootstrap.sh` script to resolve dependencies that not available on a standard Ubuntu instance.
- **File Management:** Provides an abstraction to specify a file's content and metadata (owner, group, mode).
- **Package Management:** Provides an abstraction to install and remove Debian packages.
- **Service Management:** Provides a mechanism for restarting a service when relevant files or packages are updated.
- **Idempotency:** Ensures safe application of configurations repeatedly.
- **Configuration Specification:** Configures 2 web servers capable of running the provided PHP application. IPs of the servers are in `hosts.yaml`
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

    ```sh
    ./bootstrap.sh
3. Set the Environment Variables

   Ensure that the environment variables SSH_USERNAME and SSH_PASSWORD are set with the SSH credentials.

    ```sh
    export SSH_USERNAME=root
    export SSH_PASSWORD=<password>
4. Edit Configuration Files

   Update the IP addresses in hosts.yaml to match your target hosts. Ensure your remote hosts are accessible via SSH and have the necessary permissions.

   Modify config.yaml to specify the configuration tasks you want to apply.

5. Run the Main Python File

   Execute the main script to apply the configurations to the specified hosts.

   ```py
    python3 simpleconfigmanager.py
## Configuration File (`config.yaml`)

The `config.yaml` file is used to define the configuration tasks. Each task is represented as an object with the following properties:

- `type`: The type of the task. Can be `package`, `file`, or `service`.
- `name`: The name of the package or service (required for `package` and `service` types).
- `state`: The desired state of the package or service.

### Valid States

- For `package` type:
  - `present`: Ensures the package is installed.
  - `absent`: Ensures the package is removed.

- For `service` type:
  - `start`: Starts the service.
  - `stop`: Stops the service.
  - `restart`: Restarts the service.
  - `reload`: Reloads the service configuration.

### Example Configuration

```yaml
    - type: package
    name: apache2
    state: present

    - type: package
    name: php
    state: present

    - type: file
    path: /var/www/html/index.php
    content: |
        <?php
        header("Content-Type: text/plain");
        echo "Hello, world!\n";
        exit;
        ?>
    owner: www-data
    group: www-data
    mode: "0644"
    manage_file: true

    - type: service
    name: apache2
    state: reload
```

## Logging
All actions and errors are logged to the `simpleconfigmanager.log` file. The file will be create in the same directory when the code is run. Check this file for detailed logs of the execution.

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