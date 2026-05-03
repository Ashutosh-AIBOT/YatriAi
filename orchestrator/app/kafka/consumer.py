import asyncio
import json
from aiokafka import AIOKafkaProducer
from app.config import settings

# Dummy DB dependency for alerts
async def get_active_alerts():
    # In a real scenario, this fetches from the DB: SELECT * FROM price_alerts WHERE is_active=true
    return [
        {"id": "1", "user_id": "user123", "alert_type": "flight", "reference_id": "IND-DEL", "threshold_price": 5000.0, "last_known_price": 5500.0}
    ]

# Dummy API querying function
async def check_current_price(alert_type: str, reference_id: str) -> float:
    # Simulates calling external APIs like Amadeus or Ola
    return 4800.0 # Price dropped!

async def price_monitor_loop():
    print("Starting background price monitor loop...")
    
    # Initialize Kafka Producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers
    )
    
    try:
        await producer.start()
        print("Kafka producer connected for price alerts.")
    except Exception as e:
        print(f"Warning: Could not connect to Kafka: {e}")
        # Proceed anyway for testing logic
        producer = None

    try:
        while True:
            # 1. Fetch active alerts from database
            active_alerts = await get_active_alerts()
            
            # 2. Iterate and check prices
            for alert in active_alerts:
                try:
                    current_price = await check_current_price(alert["alert_type"], alert["reference_id"])
                    
                    if current_price <= alert["threshold_price"]:
                        print(f"Price alert triggered for {alert['reference_id']}: {current_price} <= {alert['threshold_price']}")
                        
                        payload = {
                            "userId": alert["user_id"],
                            "alertId": alert["id"],
                            "type": alert["alert_type"],
                            "reference": alert["reference_id"],
                            "oldPrice": alert["last_known_price"],
                            "newPrice": current_price,
                            "message": f"Price dropped for {alert['reference_id']} to {current_price}!"
                        }
                        
                        if producer:
                            await producer.send_and_wait(
                                "price.alert",
                                json.dumps(payload).encode('utf-8')
                            )
                        
                        # In real scenario: UPDATE price_alerts SET is_active=false, notified_at=NOW()
                except Exception as inner_e:
                    print(f"Error checking price for alert {alert['id']}: {inner_e}")
                    
            # 3. Sleep before polling again
            await asyncio.sleep(60) # Poll every 60 seconds
            
    except asyncio.CancelledError:
        print("Price monitor loop cancelled.")
    finally:
        if producer:
            await producer.stop()
