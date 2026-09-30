"""One worker is required because download results live in process memory."""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = 1
threads = 2
timeout = 120
accesslog = "-"  # Use a format that does not log download bearer tokens.
access_log_format = '%(h)s %(t)s "%(m)s %(U)s %(H)s" %(s)s %(b)s %(L)s'
errorlog = "-"
