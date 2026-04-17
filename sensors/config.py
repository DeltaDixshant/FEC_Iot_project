# =============================================
# CONFIGURATION - change these values easily
# (this directly satisfies the "configurable frequency & dispatch rates" requirement)
# =============================================
FREQUENCY_SEC = 5          # How often each sensor generates a new reading
DISPATCH_RATE_SEC = 30     # How often the sensor sends the batch to the fog node
FOG_URL = "http://127.0.0.1:8000/api/sensor"   # Local fog node (we will change later for AWS)