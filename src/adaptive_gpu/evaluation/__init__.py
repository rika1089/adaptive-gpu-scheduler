"""evaluation package."""
from adaptive_gpu.evaluation.compare_policies import run_comparison
from adaptive_gpu.evaluation.summarize import (
    print_comparison_table,
    save_json,
    plot_bar_comparison,
    plot_allocation_over_time,
)
