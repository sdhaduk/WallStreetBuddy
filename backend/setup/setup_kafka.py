#!/usr/bin/env python3
"""
Script to set up Kafka topics for Reddit data streaming
"""

import time
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
TOPICS = [
    {
        'name': 'reddit-data',
        'num_partitions': 16,
        'replication_factor': 1
    },
    {
        'name': 'ticker-mentions',
        'num_partitions': 16,
        'replication_factor': 1
    }
]

def create_topics():
    """Create Kafka topics if they don't exist"""
    
    admin_client = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        client_id='reddit-setup'
    )
    
    topic_list = []
    for topic_config in TOPICS:
        if topic_config['name'] == 'reddit-data':
            topic_configs = {
                'retention.ms': '3600000', 
                'segment.ms': '600000'
            }
        else:
            topic_configs = {}
        
        topic = NewTopic(
            name=topic_config['name'],
            num_partitions=topic_config['num_partitions'],
            replication_factor=topic_config['replication_factor'],
            topic_configs=topic_configs
        )
        topic_list.append(topic)
    
    try:
        fs = admin_client.create_topics(new_topics=topic_list, validate_only=False)
    
        try:
            for topic, future in fs.items():
                try:
                    future.result() 
                    print(f"✅ Topic '{topic}' created successfully")
                except TopicAlreadyExistsError:
                    print(f"ℹ️  Topic '{topic}' already exists")
                except Exception as e:
                    print(f"❌ Failed to create topic '{topic}': {e}")
        except AttributeError:
            import time
            time.sleep(2)  
            for topic_config in TOPICS:
                print(f"✅ Topic '{topic_config['name']}' creation requested")
                
    except Exception as e:
        print(f"❌ Error creating topics: {e}")
    
    finally:
        admin_client.close()

def wait_for_kafka():
    """Wait for Kafka to be ready"""
    print("⏳ Waiting for Kafka to be ready...")
    
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                client_id='kafka-health-check'
            )
            
            metadata = admin_client.describe_topics()
            admin_client.close()
            
            print("✅ Kafka is ready!")
            return True
            
        except Exception as e:
            retry_count += 1
            print(f"⏳ Kafka not ready yet (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(2)
    
    print("❌ Kafka failed to start within timeout period")
    return False

def main():
    """Main setup function"""
    print("🚀 Setting up Kafka for Reddit data streaming...")
    
    if not wait_for_kafka():
        print("❌ Setup failed: Kafka is not available")
        return
    
    create_topics()
    
    print("\n🎉 Kafka setup complete!")
    print("\n📋 Next steps:")
    print("1. Start the producer: python kafka_producer.py")
    print("2. Start the consumer: python kafka_consumer.py")
    print("3. Check Kafka UI at: http://localhost:8080")

if __name__ == "__main__":
    main()