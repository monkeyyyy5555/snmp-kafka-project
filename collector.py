import argparse
import asyncio
import json
import logging
import signal
import time
from datetime import datetime, timezone

from kafka import KafkaProducer
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, get_cmd,
)
from common import TOPIC, settings, ensure_topic
from rates import Rates

LOG = logging.getLogger("collector")

async def poll(engine, cfg, ip, index, name):
    target = await UdpTransportTarget.create((ip, 161), timeout=2, retries=0)
    oids = [
        f"1.3.6.1.2.1.2.2.1.10.{index}",
        f"1.3.6.1.2.1.2.2.1.16.{index}",
        "1.3.6.1.2.1.1.3.0",
        f"1.3.6.1.2.1.31.1.1.1.19.{index}",
        f"1.3.6.1.2.1.2.2.1.5.{index}",
        f"1.3.6.1.2.1.2.2.1.2.{index}",
    ]
    error, status, _, bindings = await get_cmd(
        engine, CommunityData(cfg["community"], mpModel=1), target, ContextData(),
        *(ObjectType(ObjectIdentity(oid)) for oid in oids), lookupMib=False)
    if error or status:
        raise RuntimeError("SNMP request failed")
    values = [int(binding[1]) for binding in bindings[:5]]
    if str(bindings[5][1]) != name:
        raise ValueError("Configured interface does not match ifDescr")
    return values

async def collect_one(engine, cfg, producer, rates, ip, index, name):
    key = (ip, index)
    try:
        incoming, outgoing, uptime, disc, speed = await poll(engine, cfg, ip, index, name)
        now = time.monotonic()
        in_rate, out_rate = rates.sample(key, (incoming, outgoing), now, uptime, disc, speed)
        event = dict(timestamp=datetime.now(timezone.utc).isoformat(),
                     router_ip=ip, interface=name, if_index=index,
                     in_octets=incoming, out_octets=outgoing,
                     in_mbps=in_rate, out_mbps=out_rate)
        future = producer.send(TOPIC, key=f"{ip}:{index}".encode(), value=event)
        metadata = await asyncio.to_thread(future.get, timeout=10)
        print(json.dumps(dict(event=event, partition=metadata.partition, offset=metadata.offset)), flush=True)
        return True
    except Exception as exc:
        rates.reset(key)
        # Never print exception content: third-party errors might contain credentials.
        LOG.warning("Sample failed router=%s index=%s error=%s", ip, index, type(exc).__name__)
        return False

async def run(args):
    cfg = settings()
    ensure_topic(cfg["bootstrap"])
    producer = KafkaProducer(bootstrap_servers=cfg["bootstrap"], acks="all",
                             retries=0, max_block_ms=5000, request_timeout_ms=5000,
                             value_serializer=lambda x: json.dumps(x).encode())
    engine, rates, stop = SnmpEngine(), Rates(), asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    successes = 0
    try:
        cycle = 0
        while not stop.is_set() and (args.samples == 0 or cycle < args.samples):
            started = time.monotonic()
            results = await asyncio.gather(*(
                collect_one(engine, cfg, producer, rates, ip, index, name)
                for ip in cfg["routers"] for index, name in cfg["interfaces"]))
            successes += sum(results)
            cycle += 1
            if args.samples and cycle >= args.samples:
                break
            try:
                await asyncio.wait_for(stop.wait(), max(0.001, cfg["interval"] - (time.monotonic()-started)))
            except TimeoutError:
                pass
    finally:
        engine.close_dispatcher()
        producer.close(timeout=10)
    return 0 if successes else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=0, help="Poll cycles; 0 runs until Ctrl+C")
    args = parser.parse_args()
    if args.samples < 0:
        parser.error("--samples must be nonnegative")
    logging.basicConfig(level=logging.WARNING)
    try:
        raise SystemExit(asyncio.run(run(args)))
    except Exception as exc:
        LOG.error("Collector stopped: %s", type(exc).__name__)
        raise SystemExit(1)
