"""
Core App Configuration

This module configures the core Django app, handling signal registration,
startup checks, and initialization tasks.
"""

import logging
import os
import socket
from typing import Any, Optional

import psutil
from django.apps import AppConfig
from django.conf import settings
from django.db.models import QuerySet

# Configure logging
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Base exception for configuration-related errors."""


class InvalidSettingError(ConfigurationError):
    """Exception raised for invalid setting values."""


class IncompatibleSettingsError(ConfigurationError):
    """Exception raised for incompatible setting combinations."""


class EnvironmentConfigurationError(ConfigurationError):
    """Exception raised for environment-specific configuration issues."""


class ResourceError(Exception):
    """Exception raised for resource-related issues."""


class CoreConfig(AppConfig):
    """
    Configuration for the core Django app.

    Handles app initialization, signal registration, and startup tasks.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core"

    # System resource thresholds
    MIN_DISK_SPACE_MB: int = 500
    MIN_MEMORY_MB: int = 1024
    MAX_CPU_PERCENT: float = 95.0 if settings.DEBUG else 90.0
    # Minimum acceptable disk read speed in MB/s
    MIN_DISK_READ_SPEED_MB: float = 10.0
    # Minimum acceptable disk write speed in MB/s
    MIN_DISK_WRITE_SPEED_MB: float = 5.0
    # Maximum acceptable disk usage percentage
    MAX_DISK_USAGE_PERCENT: float = 90.0
    # Maximum acceptable memory usage percentage
    MAX_MEMORY_USAGE_PERCENT: float = 90.0 if settings.DEBUG else 85.0
    # Maximum acceptable swap usage percentage
    MAX_SWAP_USAGE_PERCENT: float = 85.0 if settings.DEBUG else 60.0
    # Maximum acceptable process memory usage
    MAX_PROCESS_MEMORY_PERCENT: float = 30.0
    # Maximum acceptable process CPU usage
    MAX_PROCESS_CPU_PERCENT: float = 50.0
    # Timeout for local network checks in seconds
    NETWORK_TIMEOUT_LOCAL: float = 1.0
    # Timeout for external network checks in seconds
    NETWORK_TIMEOUT_EXTERNAL: float = 3.0

    # Configuration validation constants
    PRODUCTION_REQUIRED_SETTINGS = {
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SECURE_HSTS_SECONDS",
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    }

    DEVELOPMENT_RECOMMENDED_SETTINGS = {
        "DEBUG_TOOLBAR",
        "INTERNAL_IPS",
    }

    INCOMPATIBLE_SETTINGS = [
        # Debug and SSL redirect shouldn't be enabled together
        ("DEBUG", "SECURE_SSL_REDIRECT"),
        # Debug and secure session cookies
        ("DEBUG", "SESSION_COOKIE_SECURE"),
    ]

    def check_system_resources(self) -> None:
        """
        Check system resources meet minimum requirements.

        Verifies available disk space, memory, CPU usage, disk I/O,
        and network connectivity.

        Raises:
            ResourceError: If system resources are insufficient
            RuntimeError: If resource checks fail unexpectedly
        """
        # Skip resource checks in development mode
        if settings.DEBUG:
            return

        resource_errors = []

        try:
            # Check disk space
            try:
                disk_usage = psutil.disk_usage(os.path.abspath(os.sep))
                free_disk_mb = disk_usage.free / (1024 * 1024)  # Convert to MB
                disk_percent = disk_usage.percent

                if free_disk_mb < self.MIN_DISK_SPACE_MB:
                    msg = (
                        f"Insufficient disk space. Required: {self.MIN_DISK_SPACE_MB}MB, "
                        f"Available: {free_disk_mb:.2f}MB"
                    )
                    resource_errors.append(msg)
                elif disk_percent > self.MAX_DISK_USAGE_PERCENT:
                    msg = (
                        f"High disk usage: {disk_percent}%. Consider freeing up space."
                    )
                    logger.warning(msg)
            except Exception as e:
                resource_errors.append(f"Failed to check disk space: {str(e)}")

            # Check memory - more detailed
            try:
                memory = psutil.virtual_memory()
                available_memory_mb = memory.available / (1024 * 1024)  # Convert to MB
                total_memory_mb = memory.total / (1024 * 1024)
                memory_percent = memory.percent
                swap = psutil.swap_memory()
                swap_percent = swap.percent

                if available_memory_mb < self.MIN_MEMORY_MB:
                    msg = (
                        f"Insufficient memory. Required: {self.MIN_MEMORY_MB}MB, "
                        f"Available: {available_memory_mb:.2f}MB"
                    )
                    resource_errors.append(msg)

                # Memory usage warnings
                if memory_percent > self.MAX_MEMORY_USAGE_PERCENT:
                    msg = (
                        f"High memory usage: {memory_percent}%. "
                        f"Total: {total_memory_mb:.0f}MB, "
                        f"Available: {available_memory_mb:.0f}MB"
                    )
                    logger.warning(msg)

                if swap_percent > self.MAX_SWAP_USAGE_PERCENT:
                    msg = (
                        f"High swap usage: {swap_percent}%. "
                        "System performance may be degraded."
                    )
                    logger.warning(msg)
            except Exception as e:
                resource_errors.append(f"Failed to check memory: {str(e)}")

            # Check CPU usage with load average
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                load_avg = psutil.getloadavg()
                cpu_count = psutil.cpu_count()

                if cpu_percent > self.MAX_CPU_PERCENT:
                    msg = (
                        f"High CPU usage. Maximum: {self.MAX_CPU_PERCENT}%, "
                        f"Current: {cpu_percent}%"
                    )
                    resource_errors.append(msg)

                # Check if load average is too high (> 2x number of CPUs)
                if load_avg[0] > (cpu_count * 2):
                    msg = (
                        f"High system load: {load_avg[0]:.1f}. "
                        f"Number of CPUs: {cpu_count}"
                    )
                    logger.warning(msg)
            except Exception as e:
                resource_errors.append(f"Failed to check CPU usage: {str(e)}")

            # Check disk I/O
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    read_speed = disk_io.read_bytes / (1024 * 1024)  # MB
                    write_speed = disk_io.write_bytes / (1024 * 1024)  # MB

                    if disk_io.read_time > 0:  # Avoid division by zero
                        avg_read_speed = read_speed / (disk_io.read_time / 1000)  # MB/s
                        if avg_read_speed < self.MIN_DISK_READ_SPEED_MB:
                            msg = f"Slow disk read speed: {avg_read_speed:.1f}MB/s"
                            logger.warning(msg)

                    if disk_io.write_time > 0:  # Avoid division by zero
                        avg_write_speed = write_speed / (disk_io.write_time / 1000)
                        if avg_write_speed < self.MIN_DISK_WRITE_SPEED_MB:
                            msg = f"Slow disk write speed: {avg_write_speed:.1f}MB/s"
                            logger.warning(msg)
            except Exception as e:
                logger.warning(f"Unable to check disk I/O performance: {str(e)}")

            # Check network connectivity only in production mode
            if not settings.DEBUG:
                # Check network connectivity
                try:
                    # Try connecting to common DNS ports
                    dns_servers = [
                        ("8.8.8.8", 53),  # Google DNS
                        ("1.1.1.1", 53),  # Cloudflare DNS
                    ]

                    connected = False
                    for server, port in dns_servers:
                        try:
                            t = self.NETWORK_TIMEOUT_EXTERNAL
                            with socket.create_connection((server, port), timeout=t):
                                connected = True
                                break
                        except socket.error:
                            continue

                    if not connected:
                        resource_errors.append(
                            "Unable to establish network connectivity"
                        )

                except Exception as e:
                    logger.warning(f"Failed to check network connectivity: {str(e)}")

            # Process monitoring
            try:
                process = psutil.Process()
                process_memory = process.memory_info().rss / (1024 * 1024)  # MB
                process_cpu = process.cpu_percent(interval=1)

                max_memory = total_memory_mb * (self.MAX_PROCESS_MEMORY_PERCENT / 100)
                if process_memory > max_memory:
                    memory_percent = (process_memory / total_memory_mb) * 100
                    msg = (
                        f"High process memory usage: {process_memory:.0f}MB "
                        f"({memory_percent:.1f}% of total)"
                    )
                    logger.warning(msg)

                if process_cpu > self.MAX_PROCESS_CPU_PERCENT:
                    logger.warning(f"High process CPU usage: {process_cpu}%")
            except Exception as e:
                logger.warning(f"Unable to check process resources: {str(e)}")

            if resource_errors:
                error_msg = "\n".join(resource_errors)
                logger.error(f"System resource check failed:\n{error_msg}")
                raise ResourceError(error_msg)

            msg = (
                f"System resources OK - Memory: {memory_percent}%, "
                f"CPU: {cpu_percent}%, Disk: {disk_percent}%"
            )
            logger.info(msg)

        except ResourceError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error during system resource check: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def ready(self):
        """
        Initialize app and perform startup checks.

        Called by Django when the app is ready. Performs system resource checks,
        validates settings, and registers signal handlers.
        """
        try:
            # Check system resources
            self.check_system_resources()

            # Register signal handlers
            from . import signals  # noqa

            # Additional initialization can be added here

        except Exception as e:
            logger.error(f"Error during app initialization: {str(e)}")
            raise

    def get_procedure_code_by_code(self, code: str) -> Optional[Any]:
        """Get procedure code by code."""
        from core.models import ProcedureCode

        try:
            return ProcedureCode.objects.get(code=code)
        except ProcedureCode.DoesNotExist:
            return None

    def get_procedure_codes_by_category(self, category: str) -> QuerySet[Any]:
        """Get procedure codes by category."""
        from core.models import ProcedureCode

        return ProcedureCode.objects.filter(category=category)
