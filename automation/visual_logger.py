"""
Visual execution logger with colored terminal output and progress tracking.

Provides real-time visual feedback during browser automation execution.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from enum import Enum

from automation.config import AutomationConfig


class Color(Enum):
    """ANSI color codes for terminal output."""
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class StepStatus(Enum):
    """Status of execution steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class VisualLogger:
    """
    Visual execution logger with colored output and progress tracking.
    
    Features:
    - Colored terminal output for different action types
    - Real-time progress bar
    - Step-by-step execution tracking
    - Execution summary
    - Error visualization
    """
    
    def __init__(self, total_steps: int = 10, enabled: bool = None):
        """
        Initialize visual logger.
        
        Args:
            total_steps: Total number of steps in the workflow
            enabled: Whether visual logging is enabled (default from config)
        """
        if enabled is None:
            enabled = AutomationConfig.DEBUG_MODE or AutomationConfig.VISUAL_MODE
        
        self.enabled = enabled
        self.total_steps = total_steps
        self.current_step = 0
        self.steps: List[Dict] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Milestone tracking
        self.milestones: List[str] = []
        self.screenshots: List[Path] = []
    
    def _colorize(self, text: str, color: Color) -> str:
        """Apply color to text."""
        if not self.enabled:
            return text
        return f"{color.value}{text}{Color.RESET.value}"
    
    def _bold(self, text: str) -> str:
        """Apply bold formatting to text."""
        if not self.enabled:
            return text
        return f"{Color.BOLD.value}{text}{Color.RESET.value}"
    
    def step(self, step_number: int, action: str, status: StepStatus = StepStatus.IN_PROGRESS) -> None:
        """
        Log a step in the execution workflow.
        
        Args:
            step_number: Current step number (e.g., "1/10")
            action: Description of the action being performed
            status: Status of the step
        """
        if not self.enabled:
            return
        
        color_map = {
            StepStatus.IN_PROGRESS: Color.BLUE,
            StepStatus.COMPLETED: Color.GREEN,
            StepStatus.FAILED: Color.RED,
            StepStatus.PENDING: Color.YELLOW,
        }
        
        status_symbol = {
            StepStatus.IN_PROGRESS: "→",
            StepStatus.COMPLETED: "✓",
            StepStatus.FAILED: "✗",
            StepStatus.PENDING: "○",
        }
        
        color = color_map.get(status, Color.WHITE)
        symbol = status_symbol.get(status, "•")
        
        message = f"[{step_number}] {symbol} {action}"
        print(self._colorize(message, color))
        
        # Track step
        self.steps.append({
            "step": step_number,
            "action": action,
            "status": status,
            "timestamp": datetime.now()
        })
    
    def success(self, message: str) -> None:
        """Log a success message."""
        if not self.enabled:
            return
        print(self._colorize(f"✓ {message}", Color.GREEN))
    
    def error(self, message: str) -> None:
        """Log an error message."""
        if not self.enabled:
            return
        print(self._colorize(f"✗ {message}", Color.RED))
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        if not self.enabled:
            return
        print(self._colorize(f"⚠ {message}", Color.YELLOW))
    
    def info(self, message: str) -> None:
        """Log an info message."""
        if not self.enabled:
            return
        print(self._colorize(f"ℹ {message}", Color.CYAN))
    
    def waiting(self, message: str) -> None:
        """Log a waiting message."""
        if not self.enabled:
            return
        print(self._colorize(f"⏳ {message}", Color.YELLOW))
    
    def progress(self, current: int, total: int, current_action: str = "") -> None:
        """
        Display progress bar.
        
        Args:
            current: Current step number
            total: Total steps
            current_action: Description of current action
        """
        if not self.enabled:
            return
        
        percentage = (current / total) * 100
        bar_length = 20
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        progress_text = f"{bar} {percentage:.0f}%"
        if current_action:
            progress_text += f" - {current_action}"
        
        print(self._colorize(progress_text, Color.CYAN))
    
    def milestone(self, milestone: str) -> None:
        """
        Log a milestone in the execution.
        
        Args:
            milestone: Description of the milestone
        """
        if not self.enabled:
            return
        
        print(self._colorize(f"\n🎯 {milestone}", Color.MAGENTA))
        self.milestones.append(milestone)
    
    def screenshot(self, path: Path) -> None:
        """
        Log that a screenshot was taken.
        
        Args:
            path: Path to the screenshot
        """
        if not self.enabled:
            return
        
        print(self._colorize(f"📸 Screenshot saved: {path}", Color.CYAN))
        self.screenshots.append(path)
    
    def separator(self) -> None:
        """Print a visual separator."""
        if not self.enabled:
            return
        print(self._colorize("=" * 60, Color.WHITE))
    
    def header(self, title: str) -> None:
        """
        Print a header.
        
        Args:
            title: Header title
        """
        if not self.enabled:
            return
        
        self.separator()
        print(self._colorize(self._bold(title), Color.WHITE))
        self.separator()
    
    def start_execution(self) -> None:
        """Mark the start of execution."""
        if not self.enabled:
            return
        
        self.start_time = time.time()
        self.header("BROWSER AUTOMATION EXECUTION")
        print(self._colorize(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Color.CYAN))
        print()
    
    def end_execution(self) -> None:
        """Mark the end of execution and print summary."""
        if not self.enabled:
            return
        
        self.end_time = time.time()
        execution_time = self.end_time - self.start_time
        
        print()
        self.header("EXECUTION SUMMARY")
        
        # Print step summary
        for step in self.steps:
            status_symbol = {
                StepStatus.IN_PROGRESS: "→",
                StepStatus.COMPLETED: "✓",
                StepStatus.FAILED: "✗",
                StepStatus.PENDING: "○",
            }
            symbol = status_symbol.get(step["status"], "•")
            
            color = Color.GREEN if step["status"] == StepStatus.COMPLETED else Color.RED
            message = f"{symbol} {step['action']}"
            print(self._colorize(message, color))
        
        print()
        print(self._colorize(f"Execution Time: {execution_time:.1f} seconds", Color.CYAN))
        
        if self.screenshots:
            print(self._colorize(f"Screenshots: {len(self.screenshots)} captured", Color.CYAN))
        
        self.separator()
    
    def error_details(self, error: Exception, selector: Optional[str] = None) -> None:
        """
        Print detailed error information.
        
        Args:
            error: The exception that occurred
            selector: The selector that failed (if applicable)
        """
        if not self.enabled:
            return
        
        print()
        self.header("ERROR DETAILS")
        print(self._colorize(f"Error Type: {type(error).__name__}", Color.RED))
        print(self._colorize(f"Error Message: {str(error)}", Color.RED))
        
        if selector:
            print(self._colorize(f"Failed Selector: {selector}", Color.RED))
        
        print()
        print(self._colorize("Browser stopped at current page for inspection.", Color.YELLOW))
        print(self._colorize("Press Ctrl+C to exit or wait for auto-close.", Color.YELLOW))
    
    def print_video_info(self, video_path: Path) -> None:
        """
        Print information about recorded video.
        
        Args:
            video_path: Path to the video file
        """
        if not self.enabled:
            return
        
        print(self._colorize(f"🎥 Video recorded: {video_path}", Color.CYAN))


class ProgressTracker:
    """
    Simple progress tracker for multi-step operations.
    
    Tracks progress through a workflow and provides visual feedback.
    """
    
    def __init__(self, steps: List[str], visual_logger: VisualLogger):
        """
        Initialize progress tracker.
        
        Args:
            steps: List of step descriptions
            visual_logger: Visual logger instance
        """
        self.steps = steps
        self.visual_logger = visual_logger
        self.current_step = 0
        self.total_steps = len(steps)
    
    def next_step(self) -> str:
        """
        Move to the next step and return its description.
        
        Returns:
            Current step description
        """
        if self.current_step < self.total_steps:
            step_desc = self.steps[self.current_step]
            step_number = f"{self.current_step + 1}/{self.total_steps}"
            
            self.visual_logger.step(step_number, step_desc, StepStatus.IN_PROGRESS)
            self.visual_logger.progress(self.current_step + 1, self.total_steps, step_desc)
            
            self.current_step += 1
            return step_desc
        
        return "Completed"
    
    def complete_step(self, success: bool = True) -> None:
        """
        Mark the current step as completed.
        
        Args:
            success: Whether the step completed successfully
        """
        if self.current_step > 0:
            step_number = f"{self.current_step}/{self.total_steps}"
            step_desc = self.steps[self.current_step - 1]
            
            status = StepStatus.COMPLETED if success else StepStatus.FAILED
            self.visual_logger.step(step_number, step_desc, status)
    
    def get_progress(self) -> float:
        """
        Get current progress percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        return (self.current_step / self.total_steps) * 100 if self.total_steps > 0 else 0
