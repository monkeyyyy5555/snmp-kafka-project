# Final post-restart verification — 16 October 2026

Test interval: 15:36:27–15:37:02 Asia/Bangkok (08:36:27–08:37:02 UTC).
Project: untitledgfd. Ubuntu 192.168.159.128.
R1 192.168.159.131; R2 192.168.159.130.
Python 3.14.4; existing entry points and virtual environment verified.

## Result
One bounded run: collector --samples 8 and worker --duration 50 --max-messages 16.
Worker used latest offsets and was started before the collector.
16 fresh events, eight per router, topic snmp, partition 0, offsets 14–29.
Baseline end offset was 14; final end offset 30. Topic has one replica in sync.
All produced and consumed JSON events matched exactly by partition/offset.
Both processes exited 0; their recorded PIDs no longer existed at verification.
No persistent application was started and no unrelated processes were stopped.

Each client sent four 1000-byte-payload ICMP packets to the other: 4/4, zero loss.
OSPF remained FULL; interfaces up/up. SNMP ifIndex 3 maps to FastEthernet1/1
on both routers; index 2 maps to FastEthernet1/0.
Final R1 sample offset 29: in_octets 10086, out_octets 19519,
in_mbps 0.00667461, out_mbps 0.006770694.
Final R2 sample offset 28: in_octets 10128, out_octets 19579,
in_mbps 0.006674063, out_mbps 0.006770138.
R1's last inbound delta was 4168 octets across approximately 4.996 seconds:
4168 * 8 / 4.996 / 1,000,000 ~= 0.00667 Mbps.
Small rates are expected from a few pings; outbound counters include background
traffic. First samples are zero baselines, not measured idle rates.

## Evidence directory
/home/kla/snmp-kafka-project/evidence/2026-10-16-final/
- collector.jsonl and consumer.jsonl: raw application output from this test.
- collector.stderr.txt and consumer.stderr.txt: captured error streams (empty).
- baseline.json, exit-status.json, verification.json: boundaries and verification.
- client-pings.txt: both real console ping results.
- router-status.txt: interfaces, OSPF, ifIndex and ACL inspection.
- snmp-counters.txt: actual Ubuntu SNMP query output, no community printed.
- gns3-nodes.json: all six nodes started.
- docker-health.txt: Kafka healthy, UI running.
- gns3-partial-view.png: genuine captured GNS3 window; right edge is clipped.
- REPORT.md: this report.
No .env, keys, password values or community values were copied into this directory.

## Remaining manual screenshots
Capture full topology (fit entire diagram), OSPF FULL and bidirectional ping,
SNMP interface discovery/counters, Kafka UI snmp topic and messages at offsets
14–29, and collector/consumer output. Raw text/JSON exists for all except UI view.
The partial screenshot is not proof of a complete visible topology.
Window-state/user-input interruptions prevented completing GNS3 screenshot
framing. Terminal UI automation is unavailable through the computer-use skill;
no synthetic terminal screenshots were created. Kafka UI screenshot not captured.
Do not include .env contents or SNMP command credentials in screenshots.

## Persistence and submission status
R1/R2 NVRAM saves were verified during the preceding recovery phase.
No configuration was changed or saved during this test. Client recovery is
runtime-only; no automatic recovery was enabled.
The earlier submission zip predates the updated addresses, persistence status and
this evidence. Refresh that package from an explicit safe allowlist before final
submission. Do not distribute it as the current final package without updating.
Add student/course details and review screenshots before submitting.
The previous lab-kafka-python files and cisco.commands were untouched.
