"""
Command execution and monitoring system.

Extracted from Cwatch (Go) and enhanced for Python projects.
Provides comprehensive command execution with result tracking, multi-language support,
and performance monitoring.
"""

import asyncio
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import subprocess
import threading
import json


class CommandType(str, Enum):
    """Command types for different project ecosystems."""
    # JavaScript/TypeScript
    TYPESCRIPT_CHECK = "typescript"
    LINT_CHECK = "lint"
    TEST_RUNNER = "test"
    
    # Python
    PYTHON_CHECK = "python_check"
    PYTHON_TEST = "python_test"
    PYTHON_LINT = "python_lint"
    PYTHON_TYPE = "python_type"
    PYTHON_FORMAT = "python_format"
    PYTHON_SECURITY = "python_security"
    
    # Go
    GO_BUILD = "go_build"
    GO_TEST = "go_test"
    GO_LINT = "go_lint"
    GO_VET = "go_vet"
    GO_FMT = "go_fmt"
    
    # Rust
    CARGO_CHECK = "cargo_check"
    CARGO_TEST = "cargo_test"
    CARGO_CLIPPY = "cargo_clippy"
    CARGO_FMT = "cargo_fmt"
    
    # CI/CD
    GITHUB_ACTIONS = "github_actions"
    
    # Generic
    CUSTOM = "custom"


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str
    command_type: CommandType
    passed: bool
    issue_count: int
    file_count: int
    output: str
    duration: float  # seconds
    timestamp: float
    error: Optional[str] = None
    
    # Test-specific fields
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    
    # Additional metadata
    working_directory: Optional[str] = None
    exit_code: Optional[int] = None
    env_vars: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "command": self.command,
            "command_type": self.command_type.value,
            "passed": self.passed,
            "issue_count": self.issue_count,
            "file_count": self.file_count,
            "output": self.output,
            "duration": self.duration,
            "timestamp": self.timestamp,
            "error": self.error,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "working_directory": self.working_directory,
            "exit_code": self.exit_code,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandResult":
        """Create from dictionary."""
        return cls(
            command=data["command"],
            command_type=CommandType(data["command_type"]),
            passed=data["passed"],
            issue_count=data["issue_count"],
            file_count=data["file_count"],
            output=data["output"],
            duration=data["duration"],
            timestamp=data["timestamp"],
            error=data.get("error"),
            total_tests=data.get("total_tests", 0),
            passed_tests=data.get("passed_tests", 0),
            failed_tests=data.get("failed_tests", 0),
            working_directory=data.get("working_directory"),
            exit_code=data.get("exit_code"),
        )


class CommandRunner:
    """
    Execute and monitor commands with comprehensive result tracking.
    
    Extracted from Cwatch and enhanced with Python-specific features.
    """
    
    def __init__(
        self,
        working_dir: Optional[Path] = None,
        timeout: float = 300.0,  # 5 minutes default
        max_parallel: int = 4,
    ):
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout
        self.max_parallel = max_parallel
        self.results_history: List[CommandResult] = []
        self._semaphore = asyncio.Semaphore(max_parallel)
        self._callbacks: List[Callable[[CommandResult], None]] = []
    
    def add_result_callback(self, callback: Callable[[CommandResult], None]) -> None:
        """Add callback to be called when command completes."""
        self._callbacks.append(callback)
    
    async def run_command(
        self,
        command: str,
        command_type: CommandType,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        """Execute a single command with monitoring."""
        async with self._semaphore:
            return await self._execute_command(command, command_type, cwd, env)
    
    async def run_parallel_commands(
        self,
        commands: List[tuple[str, CommandType]],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> List[CommandResult]:
        """Execute multiple commands in parallel."""
        tasks = [
            self.run_command(cmd, cmd_type, cwd, env)
            for cmd, cmd_type in commands
        ]
        return await asyncio.gather(*tasks)
    
    async def _execute_command(
        self,
        command: str,
        command_type: CommandType,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        """Internal command execution with comprehensive monitoring."""
        start_time = time.time()
        work_dir = cwd or self.working_dir
        
        try:
            # Prepare environment
            env_vars = dict(os.environ) if env is None else {**os.environ, **env}
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=work_dir,
                env=env_vars,
            )
            
            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout
                )
                output = stdout.decode('utf-8', errors='replace') if stdout else ""
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                output = f"Command timed out after {self.timeout} seconds"
                exit_code = -1
            
            duration = time.time() - start_time
            
            # Parse output based on command type
            result = self._parse_command_output(
                command, command_type, output, exit_code, duration, str(work_dir), env_vars
            )
            
            # Store result and notify callbacks
            self.results_history.append(result)
            for callback in self._callbacks:
                try:
                    callback(result)
                except Exception as e:
                    # Don't let callback errors break the runner
                    print(f"Callback error: {e}")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            return CommandResult(
                command=command,
                command_type=command_type,
                passed=False,
                issue_count=1,
                file_count=0,
                output=f"Execution error: {str(e)}",
                duration=duration,
                timestamp=start_time,
                error=str(e),
                working_directory=str(work_dir),
                exit_code=-1,
                env_vars=env_vars,
            )
    
    def _parse_command_output(
        self,
        command: str,
        command_type: CommandType,
        output: str,
        exit_code: int,
        duration: float,
        work_dir: str,
        env_vars: Dict[str, str],
    ) -> CommandResult:
        """Parse command output based on command type."""
        passed = exit_code == 0
        issue_count = 0
        file_count = 0
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        # Type-specific parsing
        if command_type == CommandType.PYTHON_TEST:
            total_tests, passed_tests, failed_tests, issue_count = self._parse_python_test_output(output)
        elif command_type == CommandType.PYTHON_LINT:
            issue_count, file_count = self._parse_python_lint_output(output)
        elif command_type == CommandType.PYTHON_TYPE:
            issue_count, file_count = self._parse_python_type_output(output)
        elif command_type == CommandType.TYPESCRIPT_CHECK:
            issue_count, file_count = self._parse_typescript_output(output)
        elif command_type == CommandType.LINT_CHECK:
            issue_count, file_count = self._parse_lint_output(output)
        elif command_type == CommandType.GO_TEST:
            total_tests, passed_tests, failed_tests, issue_count = self._parse_go_test_output(output)
        
        return CommandResult(
            command=command,
            command_type=command_type,
            passed=passed,
            issue_count=issue_count,
            file_count=file_count,
            output=output,
            duration=duration,
            timestamp=time.time(),
            error=None if passed else f"Command failed with exit code {exit_code}",
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            working_directory=work_dir,
            exit_code=exit_code,
            env_vars=env_vars,
        )
    
    def _parse_python_test_output(self, output: str) -> tuple[int, int, int, int]:
        """Parse pytest output for test counts."""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        lines = output.split('\n')
        for line in lines:
            # Look for pytest summary line like "3 passed, 1 failed"
            if "passed" in line and ("failed" in line or "error" in line):
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        passed_tests = int(parts[i-1])
                    elif part in ["failed", "error"] and i > 0:
                        failed_tests += int(parts[i-1])
                total_tests = passed_tests + failed_tests
        
        issue_count = failed_tests
        return total_tests, passed_tests, failed_tests, issue_count
    
    def _parse_python_lint_output(self, output: str) -> tuple[int, int]:
        """Parse Python linting output (flake8, pylint, etc.)."""
        lines = output.split('\n')
        issue_count = 0
        files = set()
        
        for line in lines:
            if ':' in line and any(level in line for level in ['E', 'W', 'F', 'C', 'R']):
                issue_count += 1
                # Extract filename
                parts = line.split(':')
                if parts:
                    files.add(parts[0])
        
        return issue_count, len(files)
    
    def _parse_python_type_output(self, output: str) -> tuple[int, int]:
        """Parse mypy output for type checking."""
        lines = output.split('\n')
        issue_count = 0
        files = set()
        
        for line in lines:
            if ': error:' in line or ': warning:' in line:
                issue_count += 1
                # Extract filename
                if ':' in line:
                    filename = line.split(':')[0]
                    files.add(filename)
        
        return issue_count, len(files)
    
    def _parse_typescript_output(self, output: str) -> tuple[int, int]:
        """Parse TypeScript compiler output."""
        lines = output.split('\n')
        issue_count = 0
        files = set()
        
        for line in lines:
            if '(' in line and ')' in line and ':' in line:
                # TypeScript error format: filename(line,col): error message
                issue_count += 1
                filename = line.split('(')[0]
                files.add(filename)
        
        return issue_count, len(files)
    
    def _parse_lint_output(self, output: str) -> tuple[int, int]:
        """Parse general linting output (ESLint, etc.)."""
        lines = output.split('\n')
        issue_count = 0
        files = set()
        
        for line in lines:
            if 'error' in line.lower() or 'warning' in line.lower():
                issue_count += 1
                # Try to extract filename
                parts = line.split()
                if parts and '.' in parts[0]:
                    files.add(parts[0])
        
        return issue_count, len(files)
    
    def _parse_go_test_output(self, output: str) -> tuple[int, int, int, int]:
        """Parse Go test output."""
        lines = output.split('\n')
        passed_tests = 0
        failed_tests = 0
        
        for line in lines:
            if line.startswith("--- PASS:"):
                passed_tests += 1
            elif line.startswith("--- FAIL:"):
                failed_tests += 1
        
        total_tests = passed_tests + failed_tests
        issue_count = failed_tests
        return total_tests, passed_tests, failed_tests, issue_count
    
    def get_latest_results(self) -> Dict[CommandType, CommandResult]:
        """Get latest result for each command type."""
        latest = {}
        for result in self.results_history:
            if result.command_type not in latest or result.timestamp > latest[result.command_type].timestamp:
                latest[result.command_type] = result
        return latest
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of all command statuses."""
        latest = self.get_latest_results()
        
        summary = {
            "timestamp": time.time(),
            "total_commands": len(latest),
            "passed_commands": sum(1 for r in latest.values() if r.passed),
            "failed_commands": sum(1 for r in latest.values() if not r.passed),
            "total_issues": sum(r.issue_count for r in latest.values()),
            "commands": {cmd_type.value: result.to_dict() for cmd_type, result in latest.items()},
        }
        
        return summary
    
    def clear_history(self) -> None:
        """Clear all stored results."""
        self.results_history.clear()