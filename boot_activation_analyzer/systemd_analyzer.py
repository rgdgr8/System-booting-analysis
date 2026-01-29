import statistics
from datetime import datetime, timezone
from typing import List
import re

from .ssh_client import run_command
from .models import (
    ServiceEntry,
    SummaryStatistics,
    Summary,
    AnalysisResult,
)


def get_all_services(ssh_client) -> List[str]:
    """
    Retrieve all systemd services.
    """
    cmd = (
        "systemctl list-units "
        "--type=service "
        "--all "
        "--no-pager "
        "--no-legend "
        "--plain"
    )

    output = run_command(ssh_client, cmd)

    services: List[str] = []

    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        services.append(line.split()[0])

    return services


def get_service_timing(ssh_client, service_name: str) -> ServiceEntry | None:
    """
    Retrieve activation timing for a specific service.
    Returns None if timing data is invalid or unavailable.
    """
    cmd = (
        f"systemctl show {service_name} "
        "-p InactiveExitTimestampMonotonic "
        "-p ExecMainStartTimestampMonotonic "
    )

    output = run_command(ssh_client, cmd)

    data: dict[str, str] = {}

    for line in output.strip().split("\n"):
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value

    try:
        inactive_exit = int(data.get("InactiveExitTimestampMonotonic", "0"))
        exec_start = int(data.get("ExecMainStartTimestampMonotonic", "0"))
    except ValueError:
        return None

    if inactive_exit <= 0 or exec_start <= 0 or exec_start < inactive_exit:
        return None

    return ServiceEntry(
        service_name=service_name,
        inactive_exit_timestamp=inactive_exit,
        execstart_timestamp=exec_start,
        activation_latency_seconds=(exec_start - inactive_exit) / 1_000_000,
        activation_phase="",  # will be assigned later
    )


def compute_summary(results: List[ServiceEntry]) -> SummaryStatistics:
    """
    Compute aggregated statistics.
    """
    if not results:
        return SummaryStatistics(
            total_services=0,
            average_latency_seconds=None,
            max_latency_seconds=None,
            min_latency_seconds=None,
        )

    latencies = [r.activation_latency_seconds for r in results]

    return SummaryStatistics(
        total_services=len(latencies),
        average_latency_seconds=statistics.mean(latencies),
        max_latency_seconds=max(latencies),
        min_latency_seconds=min(latencies),
    )


def get_boot_userspace_time_us(ssh_client) -> int:
    """
    Retrieve the userspace boot completion time in microseconds.
    """
    cmd = "systemd-analyze"
    output = run_command(ssh_client, cmd)

    match = re.search(r"\+\s+([\d.]+)s\s+\(userspace\)", output)
    if not match:
        raise RuntimeError("Could not determine boot userspace time.")

    return int(float(match.group(1)) * 1_000_000)


def analyze_boot_activation(
    ssh_client,
    hostname: str,
    username: str,
) -> AnalysisResult:
    """
    Perform complete activation analysis.
    Includes:
    - Services activated only during initial boot phase
    - Services activated later during runtime (post-boot)
    """
    # Get boot completion boundary
    boot_boundary_us = get_boot_userspace_time_us(ssh_client)

    services = get_all_services(ssh_client)

    results: List[ServiceEntry] = []

    num_boot_phase = 0
    num_runtime = 0

    for service in services:
        timing = get_service_timing(ssh_client, service)
        if not timing:
            continue

        if timing.inactive_exit_timestamp <= boot_boundary_us:
            timing.activation_phase = "Activated only during initial boot phase"
            num_boot_phase += 1
        else:
            timing.activation_phase = "Activated later during runtime"
            num_runtime += 1

        results.append(timing)

    summary_stats = compute_summary(results)

    summary = Summary(
        total_services=len(results),
        number_of_boot_phase_only_services=num_boot_phase,
        number_of_post_boot_services=num_runtime,
        overall_statistics=summary_stats,
    )

    return AnalysisResult(
        hostname=hostname,
        username=username,
        analyzed_at=datetime.now(timezone.utc),
        boot_completion_boundary_timestamp=boot_boundary_us,
        services=results,
        summary=summary,
    )
