# Architecture

![Curie architecture — Slack holds the memory; Curie checks plans and writes the record](architecture-diagram.png)

**plan → verdict · run → record updates & alerts, unprompted**

| Box | Role |
| --- | --- |
| **Slack** | The memory. `#experiments`, Lab Record (Slack List), canvases, App Home belief ledger. Nothing is copied out. |
| **Curie** | Bolt for Python · Socket Mode · EC2. Listeners (+ poller), deterministic verdict engine, tools (RTS · Lists · scholar), JSON-validated LLM client. |
| **Claude Science** | External agent that runs experiments and posts run-records into the channel. |
| **Literature** | OpenAlex · bioRxiv — last retrieval hop, capped with RTS at ≤3 searches per verdict. |

**Legend:** solid arrows = writes / acts · dashed arrows = reads.

Editable source: [`architecture-diagram.mermaid`](architecture-diagram.mermaid).
