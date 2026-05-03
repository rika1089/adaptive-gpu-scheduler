# Adaptive GPU Scheduler — System Flow

This diagram visualizes the request lifecycle and the asynchronous adaptive allocation loop.

```mermaid
sequenceDiagram
    autonumber
    participant U as User / Workload
    participant WG as WorkloadGenerator
    participant Q as Agent Queue (FIFO)
    participant AA as AdaptiveAllocator
    participant GPU as GPU Model (1 Worker)
    participant MC as MetricsCollector

    Note over U, MC: Initialization (100s simulation window)

    U->>WG: Sends LLM Requests (Arrival Rates)
    WG->>Q: Enqueue Request
    
    Note right of Q: Requests pile up here<br/>due to 1-worker limit

    loop Every 5 seconds
        AA->>Q: Poll current arrivals (lambda_i)
        AA->>AA: Calculate Demand: d_i = (lambda_i * R_i) / P_i
        AA->>GPU: Update GPU shares (g_i)
    end

    GPU->>Q: Pull next request
    GPU->>GPU: Process (scaled by GPU share)
    GPU->>MC: Log final Latency (s)
    MC->>U: Final Response
```

### Key Components:
1. **Queue (FIFO):** With `n_workers=1`, this queue becomes the bottleneck, creating the **seconds of latency** shown in the research paper.
2. **Adaptive Loop:** Independently updates GPU shares every 5 seconds using the paper's specific formula.
3. **GPU Model:** Scales the base service time (10ms-33ms) by the allocated share.
