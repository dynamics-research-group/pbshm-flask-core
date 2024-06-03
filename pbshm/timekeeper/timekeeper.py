from datetime import datetime, timezone

from flask import Blueprint

#Create the timekeeper Blueprint
bp = Blueprint("timekeeper", __name__)

# Convert datetime to nanoseconds since epoch
def datetime_to_nanoseconds_since_epoch(timestamp: datetime):
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp needs timezone info to be unambiguous.")
    
    delta = timestamp.astimezone(timezone.utc) - datetime.fromtimestamp(0, timezone.utc)
    return ((((delta.days * 24 * 60 * 60) + delta.seconds) * 1000000) + delta.microseconds) * 1000

# Convert nanoseconds since epoch to datetime
def nanoseconds_since_epoch_to_datetime(nanoseconds):
    if isinstance(nanoseconds, int):
        return datetime.fromtimestamp(int(nanoseconds * 0.000000001), timezone.utc)
    elif isinstance(nanoseconds, (float, complex)):
        raise ValueError("Input nanoseconds must be a real-valued integer.")
    else:
        raise TypeError("Input nanoseconds must be a real-valued integer.")

#Convert View
@bp.route("/convert/<int:nanoseconds>/<unit>")
def convert_nanoseconds(nanoseconds, unit):
    if isinstance(nanoseconds, int):
        pass
    elif isinstance(nanoseconds, (float, complex)):
        raise ValueError("Input nanoseconds must be a real-valued integer.")
    else:
        raise TypeError("Input nanoseconds must be a real-valued integer.")
    
    if unit == "microseconds": return str(int(nanoseconds * 0.001))
    elif unit == "milliseconds": return str(int(nanoseconds * 0.000001))
    elif unit == "seconds": return str(int(nanoseconds * 0.000000001))
    elif unit == "datetimeutc": return datetime.fromtimestamp(int(nanoseconds * 0.000000001), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    raise Exception("Unsupported unit")