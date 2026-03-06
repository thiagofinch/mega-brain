#!/usr/bin/env python3
"""
Autonomous Processor - Unattended file processing engine for Mega Brain pipeline.

Provides Queue, Loop, Recovery, and Timeout systems for autonomous operation.

Usage:
    from core.intelligence import AutonomousProcessor

    processor = AutonomousProcessor('wf-pipeline-full')
    processor.queue.add('/path/to/file.txt', priority=1)
    result = processor.run()

    # Or via CLI:
    python3 autonomous_processor.py queue add /path/to/file.txt 1
    python3 autonomous_processor.py run --timeout=600
"""

import json
import os
import signal
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import TaskOrchestrator from same package
from core.intelligence.task_orchestrator import TaskOrchestrator

# ============================================================================
# Configuration and Constants
# ============================================================================

PROJECT_DIR = Path(os.getenv('CLAUDE_PROJECT_DIR', '.')).resolve()
QUEUE_STATE_PATH = PROJECT_DIR / '.claude' / 'mission-control' / 'QUEUE-STATE.json'
STOP_SIGNAL_PATH = PROJECT_DIR / '.claude' / 'mission-control' / 'STOP-AUTONOMOUS'
PROCESSOR_STATE_PATH = PROJECT_DIR / '.claude' / 'mission-control' / 'AUTONOMOUS-STATE.json'
MONITOR_PATH = PROJECT_DIR / '.claude' / 'mission-control' / 'AUTONOMOUS-MONITOR.json'
CHECKPOINT_PATH = PROJECT_DIR / '.claude' / 'mission-control' / 'AUTONOMOUS-CHECKPOINT.json'
LOG_PATH = PROJECT_DIR / 'logs' / 'autonomous-processing.jsonl'

DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes
DEFAULT_CHECKPOINT_INTERVAL = 5  # Save checkpoint every N files
MAX_RETRIES = 3
BACKOFF_BASE = 2  # Exponential: 2^attempt seconds


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class QueueItem:
    """Represents a file in the processing queue."""
    file_path: str
    priority: int = 0  # Higher = more priority
    added_at: str = ""
    attempts: int = 0
    last_attempt: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed, timeout


@dataclass
class ProcessingResult:
    """Result of processing a single file."""
    file_path: str
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0
    attempts: int = 1


@dataclass
class ProcessorState:
    """Tracks the autonomous processor state."""
    status: str = "idle"  # idle, running, stopped, completed
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    files_processed: int = 0
    files_failed: int = 0
    current_file: Optional[str] = None


@dataclass
class MonitoringStatus:
    """Real-time status for external monitoring."""
    status: str  # idle, running, stopped, completed
    current_file: Optional[str]
    files_in_queue: int
    files_processed: int
    files_failed: int
    started_at: Optional[str]
    last_updated: str
    current_file_started: Optional[str]
    estimated_remaining_files: int
    avg_file_duration_seconds: float
    error_rate_percent: float


@dataclass
class Checkpoint:
    """Checkpoint for crash recovery."""
    version: str = "1.0.0"
    created_at: str = ""
    queue_snapshot: List[Dict[str, Any]] = field(default_factory=list)
    processor_state: Dict[str, Any] = field(default_factory=dict)
    files_processed_since_start: int = 0
    last_completed_file: Optional[str] = None


# ============================================================================
# FileQueue: FIFO Queue with Priority and Persistence
# ============================================================================

class FileQueue:
    """FIFO queue with priority support and persistence."""

    def __init__(self):
        self.items: List[QueueItem] = []
        self._load()

    def add(self, file_path: str, priority: int = 0) -> None:
        """Add file to queue. Higher priority = processed first."""
        # Check if already in queue
        for item in self.items:
            if item.file_path == file_path and item.status in ['pending', 'processing']:
                # Update priority if higher
                if priority > item.priority:
                    item.priority = priority
                self._save()
                return

        # Add new item
        item = QueueItem(
            file_path=file_path,
            priority=priority,
            added_at=datetime.utcnow().isoformat() + 'Z'
        )
        self.items.append(item)
        self._save()

    def pop(self) -> Optional[QueueItem]:
        """Get next file (highest priority first, then FIFO)."""
        pending = [item for item in self.items if item.status == 'pending']
        if not pending:
            return None

        # Sort by priority (desc) then added_at (asc)
        pending.sort(key=lambda x: (-x.priority, x.added_at))
        next_item = pending[0]
        next_item.status = 'processing'
        self._save()
        return next_item

    def peek(self) -> Optional[QueueItem]:
        """Preview next file without removing."""
        pending = [item for item in self.items if item.status == 'pending']
        if not pending:
            return None

        pending.sort(key=lambda x: (-x.priority, x.added_at))
        return pending[0]

    def mark_complete(self, file_path: str, success: bool) -> None:
        """Mark file as completed or failed."""
        for item in self.items:
            if item.file_path == file_path:
                item.status = 'completed' if success else 'failed'
                item.last_attempt = datetime.utcnow().isoformat() + 'Z'
                self._save()
                return

    def mark_timeout(self, file_path: str) -> None:
        """Mark file as timed out."""
        for item in self.items:
            if item.file_path == file_path:
                item.status = 'timeout'
                item.last_attempt = datetime.utcnow().isoformat() + 'Z'
                self._save()
                return

    def get_pending(self) -> List[QueueItem]:
        """Get all pending items."""
        return [item for item in self.items if item.status == 'pending']

    def get_failed(self) -> List[QueueItem]:
        """Get all failed items (for retry consideration)."""
        return [item for item in self.items if item.status in ['failed', 'timeout']]

    def is_empty(self) -> bool:
        """Check if queue has no pending items."""
        return len(self.get_pending()) == 0

    def size(self) -> int:
        """Return count of pending items."""
        return len(self.get_pending())

    def _load(self) -> None:
        """Load queue from disk."""
        if not QUEUE_STATE_PATH.exists():
            return

        try:
            with open(QUEUE_STATE_PATH, 'r') as f:
                data = json.load(f)

            self.items = [
                QueueItem(**item) for item in data.get('items', [])
            ]
        except Exception as e:
            print(f"Warning: Failed to load queue state: {e}", file=sys.stderr)

    def _save(self) -> None:
        """Persist queue to disk."""
        QUEUE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'version': '1.0.0',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'items': [asdict(item) for item in self.items]
        }

        with open(QUEUE_STATE_PATH, 'w') as f:
            json.dump(data, f, indent=2)

    def clear(self) -> None:
        """Clear all items."""
        self.items = []
        self._save()


# ============================================================================
# AutonomousProcessor: Main Processing Engine
# ============================================================================

class TimeoutException(Exception):
    """Raised when file processing times out."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException("Processing timeout exceeded")


class AutonomousProcessor:
    """Main autonomous processing engine."""

    def __init__(self, workflow_id: str = "wf-pipeline-full", checkpoint_interval: int = DEFAULT_CHECKPOINT_INTERVAL):
        self.queue = FileQueue()
        self.orchestrator = TaskOrchestrator(workflow_id)
        self.state = self._load_state()
        self.timeout_seconds = DEFAULT_TIMEOUT_SECONDS
        self.checkpoint_interval = checkpoint_interval
        self._files_since_checkpoint = 0
        self._durations: List[float] = []
        self._current_file_started: Optional[str] = None
        self._last_completed_file: Optional[str] = None

    def run(self, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Process files until queue empty or stop signal received.

        Args:
            timeout_seconds: Override default timeout per file

        Returns:
            Dict with stats: processed, failed, stopped_by
        """
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds

        # Clear stop signal if exists from previous run
        self._clear_stop_signal()

        # Initialize state
        self.state.status = 'running'
        self.state.started_at = datetime.utcnow().isoformat() + 'Z'
        self.state.files_processed = 0
        self.state.files_failed = 0
        self._save_state()

        # Update monitor at start
        self._update_monitor()

        stopped_by = None

        try:
            while not self.queue.is_empty() and not self._should_stop():
                # Get next file
                item = self.queue.pop()
                if not item:
                    break

                self.state.current_file = item.file_path
                self._current_file_started = datetime.utcnow().isoformat() + 'Z'
                self._save_state()

                # Update monitor before processing
                self._update_monitor()

                # Log start
                self._log_event({
                    'event': 'file_started',
                    'file': item.file_path,
                    'attempt': item.attempts + 1,
                    'priority': item.priority
                })

                # Process file
                result = self._process_file(item)

                # Track duration
                self._durations.append(result.duration_seconds)

                # Handle result
                if result.success:
                    self.queue.mark_complete(item.file_path, True)
                    self.state.files_processed += 1
                    self._last_completed_file = item.file_path
                    self._log_event({
                        'event': 'file_completed',
                        'file': item.file_path,
                        'duration': result.duration_seconds
                    })
                else:
                    # Check if should retry
                    item.attempts += 1
                    if self._should_retry(item):
                        # Re-queue with backoff
                        self._requeue_with_backoff(item)
                        self._log_event({
                            'event': 'file_requeued',
                            'file': item.file_path,
                            'attempt': item.attempts,
                            'backoff': self._calculate_backoff(item.attempts),
                            'error': result.error
                        })
                    else:
                        # Max retries exceeded
                        self.queue.mark_complete(item.file_path, False)
                        self.state.files_failed += 1
                        self._log_event({
                            'event': 'file_failed',
                            'file': item.file_path,
                            'attempts': item.attempts,
                            'error': result.error
                        })

                self._save_state()

                # Update monitor after processing
                self._update_monitor()

                # Checkpoint management
                self._files_since_checkpoint += 1
                if self._should_checkpoint():
                    self._save_checkpoint()
                    self._files_since_checkpoint = 0

            # Determine why we stopped
            if self._should_stop():
                stopped_by = 'stop_signal'
                self.state.status = 'stopped'
            else:
                stopped_by = 'queue_empty'
                self.state.status = 'completed'

        except Exception as e:
            self.state.status = 'failed'
            self._log_event({
                'event': 'processor_error',
                'error': str(e)
            })
            raise

        finally:
            self.state.stopped_at = datetime.utcnow().isoformat() + 'Z'
            self.state.current_file = None
            self._save_state()

            # Final monitor update
            self._update_monitor()

        return {
            'processed': self.state.files_processed,
            'failed': self.state.files_failed,
            'stopped_by': stopped_by,
            'status': self.state.status
        }

    def stop(self) -> None:
        """Create stop signal file."""
        STOP_SIGNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        STOP_SIGNAL_PATH.touch()

    def _should_stop(self) -> bool:
        """Check if stop signal exists."""
        return STOP_SIGNAL_PATH.exists()

    def _clear_stop_signal(self) -> None:
        """Remove stop signal file."""
        if STOP_SIGNAL_PATH.exists():
            STOP_SIGNAL_PATH.unlink()

    def _process_file(self, item: QueueItem) -> ProcessingResult:
        """
        Process a single file with timeout.

        Uses signal.alarm() for timeout on Unix.
        Wraps orchestrator.execute() call.
        """
        start_time = time.time()
        error = None
        success = False

        # Set up timeout (Unix only)
        old_handler = None
        try:
            # Try to use signal (Unix/Linux/Mac)
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(self.timeout_seconds)

            # Execute via orchestrator
            try:
                result = self.orchestrator.execute({'files': [item.file_path]})
                success = True
            except TimeoutException:
                error = f"Timeout after {self.timeout_seconds}s"
                self.queue.mark_timeout(item.file_path)
            except Exception as e:
                error = str(e)

        finally:
            # Cancel timeout
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                if old_handler:
                    signal.signal(signal.SIGALRM, old_handler)

        duration = time.time() - start_time

        return ProcessingResult(
            file_path=item.file_path,
            success=success,
            error=error,
            duration_seconds=duration,
            attempts=item.attempts + 1
        )

    def _should_retry(self, item: QueueItem) -> bool:
        """Check if item should be retried (attempts < MAX_RETRIES)."""
        return item.attempts < MAX_RETRIES

    def _calculate_backoff(self, attempts: int) -> float:
        """Calculate exponential backoff: 2^attempts seconds."""
        return BACKOFF_BASE ** attempts

    def _requeue_with_backoff(self, item: QueueItem) -> None:
        """Re-add item to queue after backoff delay."""
        # Update item status and re-add
        item.status = 'pending'
        item.last_attempt = datetime.utcnow().isoformat() + 'Z'
        # Note: Backoff is tracked but not enforced with sleep
        # Caller can decide to delay processing if needed

    def _load_state(self) -> ProcessorState:
        """Load processor state from disk."""
        if not PROCESSOR_STATE_PATH.exists():
            return ProcessorState()

        try:
            with open(PROCESSOR_STATE_PATH, 'r') as f:
                data = json.load(f)
            return ProcessorState(**data.get('state', {}))
        except Exception as e:
            print(f"Warning: Failed to load processor state: {e}", file=sys.stderr)
            return ProcessorState()

    def _save_state(self) -> None:
        """Persist processor state."""
        PROCESSOR_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'version': '1.0.0',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'state': asdict(self.state)
        }

        with open(PROCESSOR_STATE_PATH, 'w') as f:
            json.dump(data, f, indent=2)

    def _log_event(self, event: Dict[str, Any]) -> None:
        """Append event to JSONL log."""
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        event['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        with open(LOG_PATH, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def get_status(self) -> Dict[str, Any]:
        """Return current processor status."""
        return {
            'status': self.state.status,
            'started_at': self.state.started_at,
            'stopped_at': self.state.stopped_at,
            'files_processed': self.state.files_processed,
            'files_failed': self.state.files_failed,
            'current_file': self.state.current_file,
            'queue_size': self.queue.size(),
            'queue_pending': len(self.queue.get_pending()),
            'queue_failed': len(self.queue.get_failed())
        }

    def _calculate_avg_duration(self) -> float:
        """Calculate average file processing duration."""
        if not self._durations:
            return 0.0
        return sum(self._durations) / len(self._durations)

    def _update_monitor(self) -> None:
        """Update monitoring JSON file with current status."""
        total_completed = self.state.files_processed + self.state.files_failed
        error_rate = (self.state.files_failed / total_completed * 100) if total_completed > 0 else 0
        avg_duration = self._calculate_avg_duration()

        status = MonitoringStatus(
            status=self.state.status,
            current_file=self.state.current_file,
            files_in_queue=self.queue.size(),
            files_processed=self.state.files_processed,
            files_failed=self.state.files_failed,
            started_at=self.state.started_at,
            last_updated=datetime.utcnow().isoformat() + 'Z',
            current_file_started=self._current_file_started,
            estimated_remaining_files=self.queue.size(),
            avg_file_duration_seconds=avg_duration,
            error_rate_percent=round(error_rate, 1)
        )

        MONITOR_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MONITOR_PATH, 'w') as f:
            json.dump(asdict(status), f, indent=2)

    def _save_checkpoint(self) -> None:
        """Save checkpoint for crash recovery."""
        checkpoint = Checkpoint(
            version="1.0.0",
            created_at=datetime.utcnow().isoformat() + 'Z',
            queue_snapshot=[asdict(item) for item in self.queue.items],
            processor_state=asdict(self.state),
            files_processed_since_start=self.state.files_processed,
            last_completed_file=self._last_completed_file
        )

        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_PATH, 'w') as f:
            json.dump(asdict(checkpoint), f, indent=2)

        self._log_event({
            'event': 'checkpoint_saved',
            'files_processed': self.state.files_processed,
            'queue_size': self.queue.size()
        })

    def _should_checkpoint(self) -> bool:
        """Check if checkpoint should be saved (every N files)."""
        return self._files_since_checkpoint >= self.checkpoint_interval

    def _restore_from_checkpoint(self) -> bool:
        """Restore state from checkpoint if available."""
        if not CHECKPOINT_PATH.exists():
            return False

        try:
            with open(CHECKPOINT_PATH) as f:
                data = json.load(f)

            self.queue.items = [QueueItem(**item) for item in data['queue_snapshot']]
            self.queue._save()

            state_data = data['processor_state']
            self.state = ProcessorState(**state_data)

            self._log_event({
                'event': 'checkpoint_restored',
                'from_checkpoint': data['created_at'],
                'queue_size': len(self.queue.items)
            })
            return True
        except Exception as e:
            self._log_event({'event': 'checkpoint_restore_failed', 'error': str(e)})
            return False

    def resume(self) -> Dict[str, Any]:
        """Resume processing from last checkpoint."""
        restored = self._restore_from_checkpoint()
        if not restored:
            return {'success': False, 'error': 'No checkpoint found'}
        return self.run()


# ============================================================================
# CLI Interface
# ============================================================================

def print_usage():
    print("""
Autonomous Processor - Mega Brain Pipeline
===========================================

Usage:
    python3 autonomous_processor.py <command> [args]

Commands:
    queue add <file> [priority]   Add file to queue
    queue list                    List pending files
    queue clear                   Clear queue
    queue size                    Show queue size
    run [--timeout=300] [--checkpoint=N]  Start processing (checkpoint every N files, default=5)
    stop                          Send stop signal
    status                        Show processor status
    monitor                       Show real-time monitoring status
    checkpoint show               Display current checkpoint
    checkpoint clear              Remove checkpoint file
    resume                        Resume from last checkpoint
    retry-failed                  Re-queue all failed files

Examples:
    python3 autonomous_processor.py queue add inbox/file.txt 1
    python3 autonomous_processor.py run --timeout=600 --checkpoint=10
    python3 autonomous_processor.py monitor
    python3 autonomous_processor.py resume
    python3 autonomous_processor.py stop
    """)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'queue':
        if len(sys.argv) < 3:
            print_usage()
            sys.exit(1)

        subcommand = sys.argv[2].lower()
        queue = FileQueue()

        if subcommand == 'add':
            if len(sys.argv) < 4:
                print("Error: Missing file path")
                sys.exit(1)
            file_path = sys.argv[3]
            priority = int(sys.argv[4]) if len(sys.argv) > 4 else 0
            queue.add(file_path, priority)
            print(f"Added: {file_path} (priority={priority})")

        elif subcommand == 'list':
            pending = queue.get_pending()
            if not pending:
                print("Queue is empty")
            else:
                print(f"Pending files ({len(pending)}):")
                for item in pending:
                    print(f"  [{item.priority}] {item.file_path}")

        elif subcommand == 'clear':
            queue.clear()
            print("Queue cleared")

        elif subcommand == 'size':
            print(f"Queue size: {queue.size()}")

        else:
            print(f"Unknown queue command: {subcommand}")
            sys.exit(1)

    elif command == 'run':
        timeout = DEFAULT_TIMEOUT_SECONDS
        checkpoint_interval = DEFAULT_CHECKPOINT_INTERVAL
        for arg in sys.argv[2:]:
            if arg.startswith('--timeout='):
                timeout = int(arg.split('=')[1])
            elif arg.startswith('--checkpoint='):
                checkpoint_interval = int(arg.split('=')[1])

        processor = AutonomousProcessor(checkpoint_interval=checkpoint_interval)
        print(f"Starting autonomous processing (timeout={timeout}s, checkpoint every {checkpoint_interval} files)...")
        result = processor.run(timeout_seconds=timeout)
        print(f"\nCompleted:")
        print(f"  Processed: {result['processed']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Stopped by: {result['stopped_by']}")

    elif command == 'stop':
        processor = AutonomousProcessor()
        processor.stop()
        print("Stop signal sent")

    elif command == 'status':
        processor = AutonomousProcessor()
        status = processor.get_status()
        print("Processor Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    elif command == 'monitor':
        if not MONITOR_PATH.exists():
            print("No monitoring data available")
        else:
            with open(MONITOR_PATH) as f:
                data = json.load(f)
            print("Real-time Monitoring:")
            for key, value in data.items():
                print(f"  {key}: {value}")

    elif command == 'checkpoint':
        if len(sys.argv) < 3:
            print("Usage: checkpoint [show|clear]")
            sys.exit(1)

        subcommand = sys.argv[2].lower()
        if subcommand == 'show':
            if not CHECKPOINT_PATH.exists():
                print("No checkpoint available")
            else:
                with open(CHECKPOINT_PATH) as f:
                    data = json.load(f)
                print("Checkpoint:")
                print(f"  Created: {data['created_at']}")
                print(f"  Files processed: {data['files_processed_since_start']}")
                print(f"  Queue items: {len(data['queue_snapshot'])}")
                print(f"  Last file: {data['last_completed_file']}")
        elif subcommand == 'clear':
            if CHECKPOINT_PATH.exists():
                CHECKPOINT_PATH.unlink()
                print("Checkpoint cleared")
            else:
                print("No checkpoint to clear")
        else:
            print(f"Unknown checkpoint command: {subcommand}")

    elif command == 'resume':
        processor = AutonomousProcessor()
        print("Resuming from checkpoint...")
        result = processor.resume()
        if not result.get('success', True):
            print(f"Resume failed: {result.get('error')}")
        else:
            print(f"\nCompleted:")
            print(f"  Processed: {result.get('processed', 0)}")
            print(f"  Failed: {result.get('failed', 0)}")

    elif command == 'retry-failed':
        queue = FileQueue()
        failed = queue.get_failed()
        if not failed:
            print("No failed files to retry")
        else:
            for item in failed:
                item.status = 'pending'
                item.attempts = 0
            queue._save()
            print(f"Re-queued {len(failed)} failed files")

    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'AutonomousProcessor',
    'FileQueue',
    'QueueItem',
    'ProcessingResult',
    'ProcessorState',
    'MonitoringStatus',
    'Checkpoint',
]
