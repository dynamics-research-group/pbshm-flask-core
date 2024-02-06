from datetime import datetime

from flask import Blueprint
from pytz import utc

#Create the timekeeper Blueprint
bp = Blueprint("timekeeper", __name__)

# Convert datetime to nanoseconds since epoch
def datetime_to_nanoseconds_since_epoch(timestamp):
    delta = timestamp.astimezone(utc) - datetime.fromtimestamp(0, utc)
    return ((((delta.days * 24 * 60 * 60) + delta.seconds) * 1000000) + delta.microseconds) * 1000

# Convert nanoseconds since epoch to datetime
def nanoseconds_since_epoch_to_datetime(nanoseconds):
    return datetime.fromtimestamp(int(nanoseconds * 0.000000001), utc)

#Convert View
@bp.route("/convert/<int:nanoseconds>/<unit>")
def convert_nanoseconds(nanoseconds, unit):
    if unit == "microseconds": return str(int(nanoseconds * 0.001))
    elif unit == "milliseconds": return str(int(nanoseconds * 0.000001))
    elif unit == "seconds": return str(int(nanoseconds * 0.000000001))
    elif unit == "datetime": return datetime.fromtimestamp(int(nanoseconds * 0.000000001)).strftime("%Y-%m-%d %H:%M:%S")
    elif unit == "datetimeutc": return datetime.fromtimestamp(int(nanoseconds * 0.000000001), utc).strftime("%Y-%m-%d %H:%M:%S")
    raise Exception("Unsupported unit")