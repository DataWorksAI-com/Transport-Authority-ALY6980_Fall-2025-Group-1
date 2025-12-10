from src.observability.clickhouse_logger import get_clickhouse_logger
import clickhouse_connect
import uuid

print("🧪 Testing MBTA Observability Stack\n")

# Test 1: ClickHouse Logger
print("1️⃣ Testing ClickHouse Logger...")
ch_logger = get_clickhouse_logger()

# Log test conversation
conv_id = f"test_{uuid.uuid4().hex[:8]}"
ch_logger.log_conversation(
    conversation_id=conv_id,
    user_id="test_user",
    role="user",
    content="Test message for observability",
    intent="test",
    routed_to_orchestrator=True,
    metadata={"test": True}
)
print("   ✅ Logged test conversation")

# Log assistant response
ch_logger.log_conversation(
    conversation_id=conv_id,
    user_id="test_user",
    role="assistant",
    content="Test response from system",
    intent="test",
    routed_to_orchestrator=True,
    metadata={"test": True}
)
print("   ✅ Logged test response")

# Log test agent invocation
inv_id = f"inv_{uuid.uuid4().hex[:8]}"
ch_logger.log_agent_invocation(
    invocation_id=inv_id,
    conversation_id=conv_id,
    agent_name="mbta-alerts",
    duration_ms=123.45,
    status="success",
    request_payload={"test": "request"},
    response_payload={"test": "response"}
)
print("   ✅ Logged test agent invocation\n")

# Test 2: Query ClickHouse
print("2️⃣ Querying ClickHouse...\n")

client = clickhouse_connect.get_client(
    host='localhost',
    port=8123,
    username='default',
    password='clickhouse',
    database='mbta_logs'
)

# Show tables
print("📋 Tables in mbta_logs:")
result = client.query("SHOW TABLES")
for row in result.result_rows:
    print(f"   - {row[0]}")

# Query conversations
print("\n💬 Recent conversations:")
result = client.query("SELECT conversation_id, message_role, message_content FROM conversations ORDER BY timestamp DESC LIMIT 5")
if result.result_rows:
    for row in result.result_rows:
        print(f"   - [{row[1]}] {row[0]}: {row[2][:50]}...")
else:
    print("   (No conversations yet)")

# Query agent invocations
print("\n🤖 Agent invocations:")
result = client.query("SELECT agent_name, count(*) as calls, avg(duration_ms) as avg_ms FROM agent_invocations GROUP BY agent_name")
if result.result_rows:
    for row in result.result_rows:
        print(f"   - {row[0]}: {row[1]} calls, avg {row[2]:.2f}ms")
else:
    print("   (No agent invocations yet)")

# Query intents
print("\n🎯 Intent distribution:")
result = client.query("SELECT intent, count(*) as count FROM conversations WHERE intent != '' GROUP BY intent ORDER BY count DESC")
if result.result_rows:
    for row in result.result_rows:
        print(f"   - {row[0]}: {row[1]} messages")
else:
    print("   (No intents recorded yet)")

print("\n✅ Observability stack is working!")
print("\n📊 Next steps:")
print("   1. Refresh Grafana: http://localhost:3001")
print("   2. Send messages through UI: http://localhost:3000")
print("   3. Watch the dashboards update in real-time!")