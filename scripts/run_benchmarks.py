from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.api.routers.benchmarks import run_packet
from app.db import SessionLocal, init_db
from app.schemas import BenchmarkRunRequest
from app.services.simulation import seed_model_routing
from app.services.workspace import ensure_workspace


async def main() -> None:
    ensure_workspace()
    init_db()
    with SessionLocal() as db:
        seed_model_routing(db)
        root = ROOT / "benchmarks" / "v0_1" / "matters"
        for path in sorted(root.glob("*.json")):
            result = await run_packet(BenchmarkRunRequest(packet_id=path.stem), db)
            print(f"{path.stem}: sim={result.simulation_id} findings={result.metrics['useful_vulnerabilities_found']}")


if __name__ == "__main__":
    asyncio.run(main())
