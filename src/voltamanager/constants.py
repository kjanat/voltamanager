"""Constants for voltamanager."""

# Version parsing
MIN_VERSION_PARTS = 2  # Minimum number of version parts (major.minor)

# Display limits
MAX_DISPLAY_PACKAGES = 10  # Max packages to show before truncation
MAX_MAJOR_UPDATES_DISPLAY = 5  # Max major updates to show before truncation
MAX_VULNERABILITIES_DISPLAY = 20  # Max vulnerabilities to show before truncation

# Health thresholds
HEALTH_GOOD_THRESHOLD = 80  # Percentage for "good" health status
HEALTH_WARNING_THRESHOLD = 60  # Percentage for "warning" health status

# Batch query
BATCH_QUERY_MAX_PACKAGES = 4  # Max packages for batch npm query
