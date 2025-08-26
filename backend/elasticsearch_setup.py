import requests
import json
import time

ELASTICSEARCH_URL = "http://localhost:9200"

def wait_for_elasticsearch():
    """Wait for Elasticsearch to be ready"""
    print("Waiting for Elasticsearch to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{ELASTICSEARCH_URL}/_cluster/health")
            if response.status_code == 200:
                print("✅ Elasticsearch is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"Waiting... ({i+1}/{max_retries})")
        time.sleep(2)
    
    print("❌ Elasticsearch is not responding")
    return False

def create_ilm_policy():
    """Create Index Lifecycle Management policy for 7-day data retention"""
    policy = {
        "policy": {
            "phases": {
                "hot": {
                    "actions": {
                        "set_priority": {
                            "priority": 100
                        }
                    }
                },
                "delete": {
                    "min_age": "8d",
                    "actions": {
                        "delete": {}
                    }
                }
            }
        }
    }
    
    response = requests.put(
        f"{ELASTICSEARCH_URL}/_ilm/policy/ticker-mentions-policy",
        headers={"Content-Type": "application/json"},
        data=json.dumps(policy)
    )
    
    if response.status_code in [200, 201]:
        print("✅ ILM policy created successfully!")
        return True
    else:
        print(f"❌ Failed to create ILM policy: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def create_index_template():
    """Create index template for ticker-mentions indices optimized for aggregations"""
    template = {
        "index_patterns": ["ticker-mentions-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "30s",
                "index.lifecycle.name": "ticker-mentions-policy",
                "index.lifecycle.rollover_alias": "ticker-mentions"
            },
            "mappings": {
                "properties": {
                    "@timestamp": {
                        "type": "date"
                    },
                    "processed_at": {
                        "type": "date"
                    },
                    "date_only": {
                        "type": "date",
                        "format": "yyyy-MM-dd"
                    },
                    "id": {
                        "type": "keyword"
                    },
                    "subreddit": {
                        "type": "keyword"
                    },
                    "body": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "timestamp": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                    "type": {
                        "type": "keyword"
                    },
                    "tickers": {
                        "type": "keyword"
                    },
                    "ticker_count": {
                        "type": "integer"
                    },
                    "processed_timestamp": {
                        "type": "keyword"
                    }
                }
            }
        }
    }
    
    response = requests.put(
        f"{ELASTICSEARCH_URL}/_index_template/ticker-mentions-template",
        headers={"Content-Type": "application/json"},
        data=json.dumps(template)
    )
    
    if response.status_code in [200, 201]:
        print("✅ Index template created successfully!")
        return True
    else:
        print(f"❌ Failed to create index template: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def create_sample_queries():
    """Print sample Elasticsearch queries based on your requirements"""
    queries = {
        "1. Top 10 most mentioned tickers (all subreddits, last 3 days)": {
            "size": 0,
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": "now-3d/d"
                    }
                }
            },
            "aggs": {
                "ticker_mentions": {
                    "terms": {
                        "field": "tickers",
                        "size": 10,
                        "order": {"_count": "desc"}
                    }
                }
            }
        },
        
        "2. Top 10 tickers per subreddit (last 3 days)": {
            "size": 0,
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": "now-3d/d"
                    }
                }
            },
            "aggs": {
                "subreddits": {
                    "terms": {
                        "field": "subreddit",
                        "size": 10
                    },
                    "aggs": {
                        "top_tickers": {
                            "terms": {
                                "field": "tickers",
                                "size": 10,
                                "order": {"_count": "desc"}
                            }
                        }
                    }
                }
            }
        },
        
        "3. Daily mention counts for specific ticker (last 7 days)": {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "tickers": "AAPL"
                            }
                        },
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": "now-7d/d"
                                }
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "daily_counts": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "calendar_interval": "1d",
                        "format": "yyyy-MM-dd"
                    }
                }
            }
        }
    }
    
    print("\n📝 Sample Elasticsearch Queries for Your Use Cases:")
    print("=" * 60)
    for name, query in queries.items():
        print(f"\n{name}:")
        print(f"POST /ticker-mentions-*/_search")
        print(json.dumps(query, indent=2))
        print("-" * 40)

def main():
    if not wait_for_elasticsearch():
        return
    
    print("🔄 Setting up Elasticsearch for ticker data...")
    
    success = True
    if not create_ilm_policy():
        success = False
    
    if not create_index_template():
        success = False
    
    if success:
        create_sample_queries()
        print("\n🎉 Elasticsearch setup completed successfully!")
        print(f"🔍 Elasticsearch URL: {ELASTICSEARCH_URL}")
        print("📊 Index pattern: ticker-mentions-YYYY.MM.DD")
        print("🗑️  Data retention: 7 days (automatic deletion)")
        print("📈 Optimized for ticker aggregations and time-series queries")
    else:
        print("❌ Setup failed!")

if __name__ == "__main__":
    main()