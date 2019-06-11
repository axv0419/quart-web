import os

APP_CONFIG_FILE = '/appcfg/rest_service_config.json'
def _get_config():
    with open(APP_CONFIG_FILE) as f:
        config = json.load(f)
    return config


def get_config():
    config = {
        "kafka_config": {
            "bootstrap.servers": os.environ["CCLOUD_BROKER_URL"],
            "broker.version.fallback": "0.10.0.0",
            "api.version.fallback.ms": 0,
            "security.protocol": "SASL_SSL",
            "sasl.mechanisms": "PLAIN",
            "sasl.username": os.environ["CCLOUD_API_KEY"],
            # "debug": "all",
            "sasl.password": os.environ["CCLOUD_API_SECRET"]
        },
        "schema_registry": {
            "url": "http://35.246.229.124:8085"
        },
        "rest_proxy": {
            "url": "http://rest-proxy:8082/"
        }
    }
    return config
