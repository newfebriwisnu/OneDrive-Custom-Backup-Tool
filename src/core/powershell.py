"""
PowerShell command execution for OneDrive Custom Backup Tool
"""

import subprocess
import logging
from typing import Tuple
import sys


class PowerShellExecutor:
    """Handles PowerShell command execution with proper error handling"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Execute PowerShell command safely

        Args:
            command: PowerShell command to execute
            timeout: Command timeout in seconds

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            self.logger.info(f"Executing PowerShell command: {command}")

            # Use base64 encoding for complex commands to avoid quote issues
            import base64
            encoded_command = base64.b64encode(command.encode('utf-16le')).decode('ascii')
            full_command = f'powershell.exe -EncodedCommand "{encoded_command}"'

            # Execute command
            process = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )

            stdout = process.stdout.strip()
            stderr = process.stderr.strip()
            success = process.returncode == 0

            # Clean up XML progress output that PowerShell sometimes includes
            if stdout and stdout.startswith('#< CLIXML'):
                # Extract actual content from XML if any
                try:
                    import re
                    # Look for actual output between XML tags
                    match = re.search(r'<S[^>]*>([^<]+)</S>', stdout)
                    if match and not 'Error' in stdout:
                        stdout = match.group(1).replace('_x000D__x000A_', '\n')
                    else:
                        stdout = ''
                except:
                    stdout = ''
            
            if stderr and stderr.startswith('#< CLIXML'):
                # Extract error messages from XML
                try:
                    import re
                    # Extract error messages from XML
                    error_matches = re.findall(r'<S S="Error">([^<]+)</S>', stderr)
                    if error_matches:
                        # Clean up error messages
                        clean_errors = []
                        for error in error_matches:
                            clean_error = error.replace('_x000D__x000A_', '\n').strip()
                            if clean_error and not clean_error.startswith('At line:') and not clean_error.startswith('+'):
                                clean_errors.append(clean_error)
                        stderr = '\n'.join(clean_errors) if clean_errors else ''
                    else:
                        # If no error content, clear the XML noise
                        stderr = ''
                except:
                    pass

            # Special handling: If we have output but non-zero return code,
            # consider it successful for junction detection commands
            if not success and stdout and "LinkType" in command:
                success = True
                self.logger.info(
                    f"Command executed with warnings but produced output: {stdout}")
            elif success:
                self.logger.info(f"Command executed successfully: {stdout}")
            else:
                self.logger.error(
                    f"Command failed with return code {process.returncode}: {stderr}")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timeout after {timeout} seconds")
            return False, "", "Command timeout"

        except subprocess.CalledProcessError as e:
            self.logger.error(f"PowerShell command failed: {e}")
            return False, "", f"PowerShell error: {str(e)}"

        except Exception as e:
            self.logger.error(f"Unexpected error executing PowerShell: {e}")
            return False, "", f"Unexpected error: {str(e)}"

    def test_powershell_available(self) -> bool:
        """Test if PowerShell is available on the system"""
        try:
            success, _, _ = self.run_command("Get-Host", timeout=5)
            return success
        except Exception:
            return False

    def check_admin_privileges(self) -> bool:
        """Check if running with administrator privileges"""
        try:
            command = "([Security.Principal.WindowsPrincipal] " \
                "[Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(" \
                "[Security.Principal.WindowsBuiltInRole]::Administrator)"

            success, stdout, _ = self.run_command(command, timeout=5)
            if success and stdout.lower().strip() == "true":
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to check admin privileges: {e}")
            return False

    def request_admin_privileges(self) -> bool:
        """Request administrator privileges (restart application as admin)"""
        try:
            if sys.platform != "win32":
                return False

            import ctypes
            return ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            ) > 32

        except Exception as e:
            self.logger.error(f"Failed to request admin privileges: {e}")
            return False
