# # src/research_assistant/services/monitoring/system_monitor.py

# from rich.console import Console
# from rich.panel import Panel
# from rich.table import Table
# from rich.progress import Progress, SpinnerColumn, TextColumn
# from rich.live import Live
# from rich.traceback import install
# from rich.theme import Theme
# from datetime import datetime
# from typing import Dict, Any, List, Optional
# from collections import defaultdict
# import time
# import asyncio
# from contextlib import contextmanager
# from contextlib import asynccontextmanager

# # Install rich traceback handling
# install(show_locals=True)

# class ProcessStage:
#     """Enumeration of processing stages"""
#     UPLOAD = "Document Upload"
#     PARSE = "Document Parsing"
#     CHUNK = "Text Chunking"
#     EXTRACT = "Best Practice Extraction"
#     ANALYZE = "Theme Analysis"
#     VECTORIZE = "Vector Storage"
#     COMPLETE = "Process Complete"

# class MonitoringTheme:
#     """Custom color theme for monitoring"""
#     CUSTOM_THEME = Theme({
#         "info": "cyan",
#         "success": "green",
#         "warning": "yellow",
#         "error": "red",
#         "highlight": "magenta",
#         "stage": "blue",
#         "metric": "white"
#     })

# class ProcessMetrics:
#     """Metrics tracking for process monitoring"""
#     def __init__(self):
#         self.start_time = time.time()
#         self.end_time: Optional[float] = None
#         self.success = False
#         self.error: Optional[str] = None
#         self.stage_timings = {}
#         self.document_metrics = defaultdict(dict)

#     def complete(self, success: bool, error: Optional[str] = None):
#         """Complete process tracking"""
#         self.end_time = time.time()
#         self.success = success
#         self.error = error

#     @property
#     def duration(self) -> float:
#         """Get total process duration"""
#         if self.end_time is None:
#             return time.time() - self.start_time
#         return self.end_time - self.start_time

#     def add_stage_timing(self, stage: str, duration: float):
#         """Add timing for a stage"""
#         self.stage_timings[stage] = duration

#     def add_document_metric(self, doc_id: str, metric: str, value: Any):
#         """Add metric for a document"""
#         self.document_metrics[doc_id][metric] = value

# class SystemMonitor:
#     def __init__(self):
#         print("\n[SystemMonitor] Initializing monitoring system")
#         self.console = Console(theme=MonitoringTheme.CUSTOM_THEME)
#         self.metrics = ProcessMetrics()
#         self.current_stage = None
#         self._progress = None
#         print("[SystemMonitor] Monitor initialized")

#     @contextmanager  # Changed from @asynccontextmanager
#     def stage(self, stage_name: str):
#         """Context manager for stage tracking"""
#         print(f"\n[SystemMonitor.stage] Entering stage: {stage_name}")
#         try:
#             self.start_stage(stage_name)
#             start_time = time.time()
#             yield
#             duration = time.time() - start_time
#             self.complete_stage(stage_name, duration)
#             print(f"[SystemMonitor.stage] Completed stage: {stage_name} in {duration:.2f}s")
#         except Exception as e:
#             print(f"[SystemMonitor.stage] Failed stage: {stage_name} with error: {str(e)}")
#             self.fail_stage(stage_name, str(e))
#             raise

#     def start_stage(self, stage_name: str):
#         """Start a new processing stage"""
#         self.current_stage = stage_name
#         self.console.print(Panel(
#             f"[stage]Starting {stage_name}...",
#             title="Stage Start",
#             border_style="blue"
#         ))

#     def complete_stage(self, stage_name: str, duration: float):
#         """Complete a processing stage"""
#         self.metrics.add_stage_timing(stage_name, duration)
#         self.console.print(Panel(
#             f"""
#             [success]✓ {stage_name} completed
#             Duration: {duration:.2f}s
#             """,
#             title="Stage Complete",
#             border_style="green"
#         ))

#     def fail_stage(self, stage_name: str, error: str):
#         """Record stage failure"""
#         self.console.print(Panel(
#             f"""
#             [error]✗ {stage_name} failed
#             Error: {error}
#             """,
#             title="Stage Error",
#             border_style="red"
#         ))

#     @asynccontextmanager
#     async def document_progress(self, total_documents: int):
#         """Track document processing progress"""
#         self._progress = Progress(
#             SpinnerColumn(),
#             TextColumn("[progress.description]{task.description}"),
#             console=self.console
#         )
#         task_id = self._progress.add_task(
#             f"[cyan]Processing: {total_documents} documents...",
#             total=total_documents
#         )
        
#         try:
#             self._progress.start()
#             yield self._progress, task_id
#         finally:
#             self._progress.stop()

#     def log_document_metric(self, doc_id: str, metric: str, value: Any):
#         """Log metrics for a specific document"""
#         self.metrics.add_document_metric(doc_id, metric, value)
#         self.console.print(
#             f"\n [metric]Document: {doc_id}: {metric} = {value} \n"
#         )

#     def display_summary(self):
#         """Display processing summary"""
#         if not self.metrics.end_time:
#             self.metrics.complete(True)

#         # Create summary table
#         summary = Table(
#             title="Processing Summary",
#             show_header=True,
#             header_style="bold magenta"
#         )

#         summary.add_column("Metric", style="cyan")
#         summary.add_column("Value", style="yellow")

#         # Add summary rows
#         summary.add_row(
#             "Total Duration",
#             f"{self.metrics.duration:.2f}s"
#         )
#         summary.add_row(
#             "Status",
#             "[green]Success[/]" if self.metrics.success else "[red]Failed[/]"
#         )
#         if self.metrics.error:
#             summary.add_row("Error", f"[red]{self.metrics.error}[/]")

#         self.console.print(summary)

#         # Display stage timings
#         if self.metrics.stage_timings:
#             timing_table = Table(
#                 title="Stage Timings",
#                 show_header=True,
#                 header_style="bold cyan"
#             )
            
#             timing_table.add_column("Stage")
#             timing_table.add_column("Duration (s)")
#             timing_table.add_column("Percentage")
            
#             total_time = sum(self.metrics.stage_timings.values())
#             for stage, duration in self.metrics.stage_timings.items():
#                 percentage = (duration / total_time) * 100
#                 timing_table.add_row(
#                     stage,
#                     f"{duration:.2f}",
#                     f"{percentage:.1f}%"
#                 )
            
#             self.console.print(timing_table)

#         # Display document metrics
#         if self.metrics.document_metrics:
#             doc_table = Table(
#                 title="Document Metrics",
#                 show_header=True,
#                 header_style="bold blue"
#             )
            
#             doc_table.add_column("Document")
#             doc_table.add_column("Metric")
#             doc_table.add_column("Value")
            
#             for doc_id, metrics in self.metrics.document_metrics.items():
#                 for metric, value in metrics.items():
#                     doc_table.add_row(str(doc_id), metric, str(value))
            
#             self.console.print(doc_table)





###########################################################################################################################


# src/research_assistant/services/monitoring/system_monitor.py

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.traceback import install
from rich.theme import Theme
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict
import time
import asyncio
from contextlib import contextmanager, asynccontextmanager

# Install rich traceback handling
install(show_locals=True)


class ProcessStage:
    """Enumeration of processing stages"""
    INITIALIZE ="Start Processing"
    UPLOAD = "Document Upload"
    PARSE = "Document Parsing"
    CHUNK = "Text Chunking"
    EXTRACT = "Best Practice Extraction"
    ANALYSIS = "Theme Analysis"
    SEARCH = "search Document"
    VECTORIZE = "Vector Storage"
    COMPLETE = "Process Complete"


class MonitoringTheme:
    """Custom color theme for monitoring"""
    CUSTOM_THEME = Theme({
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "highlight": "magenta",
        "stage": "blue",
        "metric": "white"
    })


class AIModelCosts:
    """Track and calculate AI model usage costs"""
    
    # Cost per 1M tokens
    COSTS = {
        "gpt4-mini": {
            "base": 0.150,  # $0.150 per 1M tokens
            "cached": 0.075,  # $0.075 per 1M tokens (cached)
            "batch": 0.075   # $0.075 per 1M tokens (batch)
        },
        "embedding": {
            "base": 0.020,   # $0.020 per 1M tokens
            "batch": 0.010   # $0.010 per 1M tokens (batch)
        }
    }

    @classmethod
    def get_cost_per_token(cls, model: str, is_cached: bool = False, is_batch: bool = False) -> float:
        """Get cost per token for a specific model and usage type"""
        if model not in cls.COSTS:
            print(f"[AIModelCosts] WARNING: Unknown model {model}, using default pricing")
            return cls.COSTS["gpt4-mini"]["base"]

        if model == "gpt4-mini":
            if is_batch:
                return cls.COSTS[model]["batch"] / 1_000_000
            elif is_cached:
                return cls.COSTS[model]["cached"] / 1_000_000
            return cls.COSTS[model]["base"] / 1_000_000
        else:
            if is_batch:
                return cls.COSTS[model]["batch"] / 1_000_000
            return cls.COSTS[model]["base"] / 1_000_000

    @classmethod
    def calculate_cost(cls, tokens: int, model: str, is_cached: bool = False, is_batch: bool = False) -> float:
        """Calculate cost for token usage"""
        cost_per_token = cls.get_cost_per_token(model, is_cached, is_batch)
        total_cost = tokens * cost_per_token
        return total_cost

    @classmethod
    def format_cost(cls, cost: float) -> str:
        """Format cost for display"""
        if cost < 0.01:
            return f"${cost:.6f}"
        return f"${cost:.4f}"

class TokenUsageTracker:
    """Track token usage and costs across models"""
    
    def __init__(self):
        self.usage = defaultdict(lambda: {
            "tokens": 0,
            "cost": 0.0,
            "calls": 0
        })

    def add_usage(self, model: str, tokens: int, is_cached: bool = False, is_batch: bool = False):
        """Track usage for a model"""
        cost = AIModelCosts.calculate_cost(tokens, model, is_cached, is_batch)
        self.usage[model]["tokens"] += tokens
        self.usage[model]["cost"] += cost
        self.usage[model]["calls"] += 1

    @property
    def total_cost(self) -> float:
        """Get total cost across all models"""
        return sum(model_data["cost"] for model_data in self.usage.values())

    @property
    def total_tokens(self) -> int:
        """Get total tokens across all models"""
        return sum(model_data["tokens"] for model_data in self.usage.values())

    def get_usage_table(self) -> Table:
        """Create rich table of usage stats"""
        table = Table(
            title="AI Model Usage",
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Model", style="cyan")
        table.add_column("Tokens", justify="right")
        table.add_column("Calls", justify="right")
        table.add_column("Cost", justify="right")
        
        for model, data in self.usage.items():
            table.add_row(
                model,
                f"{data['tokens']:,}",
                str(data['calls']),
                AIModelCosts.format_cost(data['cost'])
            )
        
        table.add_row(
            "[bold]Total[/]",
            f"[bold]{self.total_tokens:,}[/]",
            f"[bold]{sum(d['calls'] for d in self.usage.values())}[/]",
            f"[bold]{AIModelCosts.format_cost(self.total_cost)}[/]"
        )
        
        return table

# Update ProcessMetrics to include token tracking
class ProcessMetrics:
    """Enhanced metrics tracking with AI usage"""
    def __init__(self):
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.success = False
        self.error: Optional[str] = None
        self.stage_timings = {}
        self.document_metrics = defaultdict(dict)
        self.token_usage = TokenUsageTracker()

    def complete(self, success: bool, error: Optional[str] = None):
        """Complete process tracking"""
        self.end_time = time.time()
        self.success = success
        self.error = error

    @property
    def duration(self) -> float:
        """Get total process duration"""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    def add_stage_timing(self, stage: str, duration: float):
        """Add timing for a stage"""
        self.stage_timings[stage] = duration

    def add_document_metric(self, doc_id: str, metric: str, value: Any):
        """Add metric for a document"""
        self.document_metrics[doc_id][metric] = value

class SystemMonitor:
    """Enhanced system monitor with AI cost tracking"""
    def __init__(self):
        print("\n[SystemMonitor] Initializing monitoring system")
        self.console = Console(theme=MonitoringTheme.CUSTOM_THEME)
        self.metrics = ProcessMetrics()
        self.current_stage = None
        self._progress = None
        print("[SystemMonitor] Monitor initialized")

    def log_ai_response(self, response: Dict[str, Any], model: str, tokens: int, is_cached: bool = False, is_batch: bool = False):
        """Log AI model response with cost tracking"""
        self.metrics.token_usage.add_usage(model, tokens, is_cached, is_batch)
        
        cost = AIModelCosts.calculate_cost(tokens, model, is_cached, is_batch)
        
        self.console.print(Panel(
            f"""[bold cyan]AI Response Summary[/]
            Model: [yellow]{model}[/]
            Tokens Used: [green]{tokens:,}[/]
            Cost: [green]{AIModelCosts.format_cost(cost)}[/]
            Cached: [blue]{is_cached}[/]
            Batch: [blue]{is_batch}[/]
            
            [bold white]Response:[/]
            {str(response)}
            """,
            title="AI Response",
            border_style="cyan"
        ))

    

    def display_token_usage(self):
        """Display token usage summary"""
        self.console.print(self.metrics.token_usage.get_usage_table())

    @contextmanager  # Changed from @asynccontextmanager
    def stage(self, stage_name: str):
        """Context manager for stage tracking"""
        print(f"\n[SystemMonitor.stage] Entering stage: {stage_name}")
        try:
            self.start_stage(stage_name)
            start_time = time.time()
            yield
            duration = time.time() - start_time
            self.complete_stage(stage_name, duration)
            print(f"[SystemMonitor.stage] Completed stage: {stage_name} in {duration:.2f}s")
        except Exception as e:
            print(f"[SystemMonitor.stage] Failed stage: {stage_name} with error: {str(e)}")
            self.fail_stage(stage_name, str(e))
            raise

    @asynccontextmanager
    async def document_progress(self, total_documents: int):
        """Track document processing progress"""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        )
        task_id = self._progress.add_task(
            f"[cyan]Processing: {total_documents} documents...",
            total=total_documents
        )
        
        try:
            self._progress.start()
            yield self._progress, task_id
        finally:
            self._progress.stop()

    def log_document_metric(self, doc_id: str, metric: str, value: Any):
        """Log metrics for a specific document"""
        self.metrics.add_document_metric(doc_id, metric, value)
        self.console.print(
            f"\n [metric]Document: {doc_id}: {metric} = {value} \n"
        )

        # Display document metrics
        if self.metrics.document_metrics:
            doc_table = Table(
                title="Document Metrics",
                show_header=True,
                header_style="bold blue"
            )
            
            doc_table.add_column("Document")
            doc_table.add_column("Metric")
            doc_table.add_column("Value")
            
            for doc_id, metrics in self.metrics.document_metrics.items():
                for metric, value in metrics.items():
                    doc_table.add_row(str(doc_id), metric, str(value))
            
            self.console.print(doc_table)

        # Add token usage summary
        self.display_token_usage()

        # Show cost efficiency metrics
        if self.metrics.token_usage.total_tokens > 0:
            efficiency_table = Table(
                title="Cost Efficiency Metrics",
                show_header=True,
                header_style="bold blue"
            )
            efficiency_table.add_column("Metric", style="cyan")
            efficiency_table.add_column("Value", style="yellow")
            
            cost_per_token = self.metrics.token_usage.total_cost / self.metrics.token_usage.total_tokens
            efficiency_table.add_row(
                "Average Cost per Token",
                AIModelCosts.format_cost(cost_per_token)
            )
            
            self.console.print(efficiency_table)


    def start_stage(self, stage_name: str):
            """Start a new processing stage"""
            self.current_stage = stage_name
            self.console.print(Panel(
                f"[stage]Starting {stage_name}...",
                title="Stage Start",
                border_style="blue"
            ))

    def complete_stage(self, stage_name: str, duration: float):
        """Complete a processing stage"""
        self.metrics.add_stage_timing(stage_name, duration)
        self.console.print(Panel(
            f"""
            [success]✓ {stage_name} completed
            Duration: {duration:.2f}s
            """,
            title="Stage Complete",
            border_style="green"
        ))


    def fail_stage(self, stage_name: str, error: str):
        """Record stage failure"""
        self.console.print(Panel(
            f"""
            [error]✗ {stage_name} failed
            Error: {error}
            """,
            title="Stage Error",
            border_style="red"
        ))


       
