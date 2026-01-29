import argparse
import sys

from .ssh_client import create_ssh_client
from .systemd_analyzer import analyze_boot_activation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze systemd service activation timing via SSH."
    )

    parser.add_argument(
        "hostname",
        help="Hostname or IP address of target system",
    )

    parser.add_argument(
        "key",
        help="Path to SSH private key",
    )

    parser.add_argument(
        "--username",
        help="SSH target username (defaults to current local user)",
    )

    parser.add_argument(
        "--out-file",
        help="Path to store generated JSON (prints to stdout if omitted)",
    )

    args = parser.parse_args()

    try:
        ssh_client = create_ssh_client(args.hostname, args.key, args.username)
        result = analyze_boot_activation(ssh_client, args.hostname, args.username)
        ssh_client.close()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    output_json = result.model_dump_json(indent=4)

    if args.out_file:
        with open(args.out_file, "w", encoding="utf-8") as f:
            f.write(output_json)
    else:
        print(output_json)
