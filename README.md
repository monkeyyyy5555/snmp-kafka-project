# SNMP–Kafka Network Telemetry

A classroom lab that collects Cisco interface traffic counters through read-only
SNMPv2c, publishes JSON telemetry to Kafka, and displays it with a Python consumer.

```text
Cisco R1/R2 → SNMP collector.py → Kafka topic snmp → worker.py
```

## Verified environment
- Python 3.14.4, PySNMP 7.1.30, kafka-python 2.3.2.
- Kafka 4.0.0: localhost:9092; Kafka UI: localhost:8081 on Ubuntu.
- GNS3 project: untitledgfd; OSPF Area 0 between the routers.
- Current Ubuntu collector: 192.168.159.128.
- R1: 192.168.159.131; R2: 192.168.159.130.
- FastEthernet1/1: verified ifIndex 3 on each router.
- Optional FastEthernet1/0: verified ifIndex 2.
DHCP addresses can change. Verify current addresses and SNMP ACL permissions after
restarts; never infer router management addresses from GNS3 console addresses.

## Requirements and setup
Use an existing reachable Kafka broker and read-only SNMP access limited to the
collector. This repository does not provision routers or replace the Kafka stack.
Install dependencies in this project's own virtual environment:
```bash
cd snmp-kafka-project
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
test -f .env || cp .env.example .env
chmod 600 .env
```
Edit .env privately: supply SNMP_COMMUNITY and verify ROUTER_IPS.
Do not commit .env. Exported environment variables override .env.
requirements.txt specifies version ranges; requirements.lock.txt records the
versions used for verification. No Python application source contains a community.

## Run and stop
Start in separate Ubuntu terminals, from the project directory:
```bash
.venv/bin/python worker.py
```
```bash
.venv/bin/python collector.py
```
Press Ctrl+C in each terminal to stop. No background service is installed.
The collector polls every five seconds by default. Set INTERFACES in .env to
3:FastEthernet1/1 or 2:FastEthernet1/0,3:FastEthernet1/1.
Interface names are checked against the router's ifDescr.

For an optional future bounded demonstration (not required to repeat submission evidence),
start worker.py --duration 50 --max-messages 16 first, then collector.py --samples 8.
The worker defaults to new messages. --from-beginning replays oldest retained
telemetry; it does not select only the most recent test.
The worker uses no consumer group and commits no offsets.
Only topic snmp is used; the old command-automation project is independent.
The collector creates snmp only if absent, with one partition and one replica,
and validates an existing topic without resetting it.

## Message format
Actual post-restart event, partition 0 offset 29:
```json
{
  "timestamp": "2026-10-16T08:37:02.126207+00:00",
  "router_ip": "192.168.159.131",
  "interface": "FastEthernet1/1",
  "if_index": 3,
  "in_octets": 10086,
  "out_octets": 19519,
  "in_mbps": 0.00667461,
  "out_mbps": 0.006770694
}
```
Kafka values have this schema. Terminal output wraps the value in event and adds
partition and offset. Timestamps are UTC.

## Rates and reliability
Mbps = counter difference × 8 / actual monotonic elapsed seconds / 1,000,000.
Initial samples return zero as a baseline. Counter32 wrap handling is checked
against interface speed; reboots, discontinuities, implausible deltas and long
gaps cause re-baselining. Timeouts isolate the affected interface and clear its
baseline. Some unreported resets are indistinguishable from plausible wraps.
Rates include background traffic and do not measure link capacity. SNMPv2c is
unencrypted and intended here only for an ACL-restricted classroom environment.
Kafka acknowledgements are checked, but this is not an exactly-once pipeline.
A bounded collector exit of zero means at least one successful sample; inspect
per-router results for full success.

## Verified results
- 10 focused unit tests passed during implementation/readiness review.
- Final test on 16 October 2026: 16 fresh messages, eight from each router.
- Topic snmp, partition 0, offsets 14–29; producer and consumer records matched.
- Four ICMP requests in each direction: 4/4 received, no loss.
- OSPF FULL; Kafka healthy; all six GNS3 nodes running.
- Traffic reached about 0.00667 Mbps inbound and 0.00677 Mbps outbound.
- Both bounded applications exited normally. No persistent worker is running.
These are recorded results, not a claim that tests ran at repository preparation.

Tests, when needed:
```bash
.venv/bin/python -m unittest -v
```

## Evidence and restart notes
See evidence/2026-10-16-final/REPORT.md and verification.json for authentic evidence.
The full topology screenshot is in screenshots/01-gns3-full.png beneath that folder.
Kafka UI and terminal screenshots are still pending; see GITHUB_SUBMISSION.md.
Recorded output must be labelled as replayed evidence if displayed later.
R1/R2 configurations and the recovered collector ACL were saved and verified.
ipterm addresses are runtime settings; recovery scripts are provided, but no
automatic startup hook was enabled. Do not run client recovery scripts on Ubuntu.
No further reboot test was performed after the latest ACL save.
Old ZIP files and historical preparation documents are excluded from this repository.

PySNMP API reference:
https://docs.lextudio.com/pysnmp/v7.1/docs/hlapi/v3arch/asyncio/manager/cmdgen/getcmd
