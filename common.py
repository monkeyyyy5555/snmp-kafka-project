import os
from dotenv import load_dotenv

TOPIC = "snmp"

def settings():
    load_dotenv()
    community = os.environ.get("SNMP_COMMUNITY", "")
    if not community:
        raise ValueError("Set SNMP_COMMUNITY in .env or the environment")
    interval = float(os.getenv("POLL_INTERVAL", "5"))
    if interval <= 0:
        raise ValueError("POLL_INTERVAL must be positive")
    interfaces = []
    for item in os.getenv("INTERFACES", "3:FastEthernet1/1").split(","):
        index, name = item.strip().split(":", 1)
        if int(index) < 1 or not name:
            raise ValueError("Invalid interface configuration")
        interfaces.append((int(index), name))
    return dict(community=community, interval=interval,
                routers=[x.strip() for x in os.getenv("ROUTER_IPS", "192.168.65.134,192.168.65.135").split(",")],
                interfaces=interfaces,
                bootstrap=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))

def ensure_topic(bootstrap):
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import TopicAlreadyExistsError
    admin = KafkaAdminClient(bootstrap_servers=bootstrap, client_id="snmp-setup")
    try:
        if TOPIC not in admin.list_topics():
            try:
                admin.create_topics([NewTopic(TOPIC, 1, 1)])
            except TopicAlreadyExistsError:
                pass
        description = admin.describe_topics([TOPIC])[0]
        partitions = description["partitions"]
        if description.get("error_code") or len(partitions) != 1 or len(partitions[0]["replicas"]) != 1:
            raise RuntimeError("Existing snmp topic does not have one partition and one replica")
        return description
    finally:
        admin.close()
