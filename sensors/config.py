# Central config file for all sensor scripts.
# Keeping these values in one place means we can tune the system behaviour
# without hunting through every sensor file separately. This directly satisfies
# the project requirement for "configurable frequency and dispatch rates".

# How often each sensor script wakes up and takes a new reading (in seconds).
# 5 seconds gives us a decent resolution without generating too much data.
FREQUENCY_SEC = 5

# How often we bundle up the buffered readings and send them to the fog node (in seconds).
# 30 seconds means each batch will contain roughly 6 readings (30 / 5 = 6).
# Batching like this is much more efficient than sending one HTTP request per reading.
DISPATCH_RATE_SEC = 30

# The fog node's local address — all sensor scripts send their data here.
# We'll swap this out for a proper hostname/IP if the fog node moves to a different machine.
FOG_URL = "http://127.0.0.1:8000/api/sensor"