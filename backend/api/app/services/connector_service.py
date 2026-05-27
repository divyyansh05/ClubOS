import sys
import os

# Add integrations directory to Python path
INTEGRATIONS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "integrations")
)
if INTEGRATIONS_DIR not in sys.path:
    sys.path.insert(0, INTEGRATIONS_DIR)

# Import connectors using importlib to avoid relative import issues
import importlib.util

def import_connector(module_name, class_name):
    try:
        module_path = os.path.join(INTEGRATIONS_DIR, f"{module_name}.py")
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        connector_class = getattr(module, class_name)
        print(f"[CONNECTORS] Loaded {class_name} from {module_name}")
        return connector_class
    except Exception as e:
        print(f"[CONNECTORS] Failed to load {class_name} from {module_name}: {e}")
        return None

YouTubeConnector = import_connector("youtube_connector", "YouTubeConnector")
WikipediaConnector = import_connector("wikipedia_connector", "WikipediaConnector")
GA4Connector = import_connector("ga4_connector", "GA4Connector")
AdobeAnalyticsConnector = import_connector("adobe_connector", "AdobeAnalyticsConnector")

ALL_CONNECTORS = []
for connector_class in [YouTubeConnector, WikipediaConnector, GA4Connector, AdobeAnalyticsConnector]:
    if connector_class is not None:
        try:
            instance = connector_class()
            ALL_CONNECTORS.append(instance)
            print(f"[CONNECTORS] Initialized {instance.connector_id}")
        except Exception as e:
            print(f"[CONNECTORS] Failed to initialize connector: {e}")

def get_all_statuses():
    statuses = []
    for c in ALL_CONNECTORS:
        try:
            status = c.test_connection()
            if status is not None:
                statuses.append(status)
        except Exception as e:
            print(f"Error testing {c.connector_id}: {e}")
    return statuses

def get_connector_data(connector_id: str, days_back: int = 30):
    connector = next(
        (c for c in ALL_CONNECTORS if c.connector_id == connector_id),
        None
    )
    if not connector:
        return None
    result = connector.fetch(days_back=days_back)
    if not result.success:
        return {"error": result.error, "records": []}
    return {
        "connector_id": connector_id,
        "fetched_at": result.fetched_at.isoformat(),
        "records": connector.to_metric_rows(result.records)
    }
