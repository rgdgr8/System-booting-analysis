Installation and Execution instructions:

1. Run commands in terminal
    - python3 -m venv venv
    - source venv/bin/activate
    - pip install .
2. Run the program with the following command in terminal
    - time-to-execstart-analyzer [-h] [--username USERNAME] [--out-file OUT_FILE] hostname key
    
    * Positional Arguments:
        • hostname: hostname or IP to connect to
        • key: path to ssh key to connect to the target
        options:
        • -h,--help: show help message and exit
        • --username: SSH target username (defaults to current local user)
        • --out-file: Path to store the generated json to (if omitted json shall be printed stdout instead)

Prerequisites:

1. Requires python 3.10 or above
2. SSH target should already trust the client (i.e. should already have the public key of the client stored)

Output (JSON):

{
    hostname: IP address of the SSH target machine
    username: Username of the SSH target machine's user
    analyzed_at: Date-time timestamp for when the output was produced
    boot_completion_boundary_timestamp: Machine timestamp in microseconds for target machine boot completion
    services: A list of objects where each object provides the Details of a service *
    summary: {
        total_services: Total number of services in the output,
        number_of_boot_phase_only_services: Number of services that activated only before the boot completion,
        number_of_post_boot_services: Number of services that activated after the boot completion,
        overall_statistics: {
            average_latency_seconds: Average latency in seconds
            median_latency_seconds: Median latency in seconds
            stddev_latency_seconds: Latency standard deviation in seconds
            max_latency_seconds: Maximum latency
            min_latency_seconds: Minimum latency
        }
    }
}

* Details of a service:

{
    service_name: Name of the service
    inactive_exit_timestamp: Monotonic machine timestamp in microseconds for when the service exited inactive state
    execstart_timestamp: Monotonic machine timestamp in microseconds for when the ExecStart command was executed for the service
    activation_latency_seconds: Latency between exiting inactive state and execution of Execstart command in seconds
    activation_phase: Describes whether the service activated only before the boot completion or after the boot completion
}

Functional description of the code:

1. ./time-to-execstart-analyzer.py
    - Entry point into the program
    - Calls cli.py

2. ./boot_activation_analyzer/cli.py
    - Parses the command line arguments
    - Calls ssh_client.py and systemd_analyzer.py
    - Prints/Writes final output

3. ./boot_activation_analyzer/models.py
    - Defines the JSON schema in python code for strict checking

4. ./boot_activation_analyzer/ssh_client.py
    - Retrieves private key from client machine
    - Logs into target using SSH
    - Runs commands on target machine

5. ./boot_activation_analyzer/systemd_analyzer.py
    - Formulates the necessary commands and uses the run_command function in ssh_client.py to run them in the target machine and get the output
    - Parses and processes the output of the commands to get the required results
    - Uses the json schema from models.py to produce the output and returns it.

Edge cases and Assumptions:

1. Services which have inactive_exit_timestamp > execstart_timestamp are being ignored even if they have been activated, since there is no method to calculate the required time interval for these services.

2. systemd-analyze userspace time has been assumed to be the boot completion time because any other alternative for example the timestamp which can be acquired using the command 'systemctl show default.target -p ActiveEnterTimestampMonotonic' is not reliable if default.target service is restarted.

3. Only the most recent run of each service has been considered for our analysis because getting information about previous/intial run requires historical data which is not available with systemctl and using journal-based event reconstruction (e.g. using journald) is not reliable due to potential inaccuracies and journal refresh.