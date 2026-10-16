import argparse
import json
import os
import signal
import time
from dotenv import load_dotenv
from kafka import KafkaConsumer
from common import TOPIC

def run(args):
    load_dotenv()
    consumer = KafkaConsumer(
        TOPIC, bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        group_id=None, enable_auto_commit=False,
        auto_offset_reset="earliest" if args.from_beginning else "latest",
        value_deserializer=lambda value: json.loads(value.decode()))
    stop = False
    def halt(*_):
        nonlocal stop
        stop = True
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, halt)
    start, count = time.monotonic(), 0
    try:
        while not stop and (not args.duration or time.monotonic()-start < args.duration):
            batches = consumer.poll(timeout_ms=500, max_records=100)
            for messages in batches.values():
                for msg in messages:
                    print(json.dumps(dict(event=msg.value, partition=msg.partition, offset=msg.offset)), flush=True)
                    count += 1
                    if args.max_messages and count >= args.max_messages:
                        return 0
    finally:
        consumer.close()
    return 0 if count else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=0, help="Seconds; 0 until Ctrl+C")
    parser.add_argument("--max-messages", type=int, default=0)
    parser.add_argument("--from-beginning", action="store_true")
    args = parser.parse_args()
    if args.duration < 0 or args.max_messages < 0:
        parser.error("Bounds must be nonnegative")
    raise SystemExit(run(args))
