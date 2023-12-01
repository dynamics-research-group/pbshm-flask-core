from flask import Blueprint, current_app, g, render_template, request, session, redirect, url_for, jsonify
from pbshm.authentication.authentication import authenticate_request
from pbshm.db import structure_collection
from datetime import datetime
from pytz import utc
from bokeh import colors
from bokeh.plotting import figure
from bokeh.models import CustomJSTickFormatter, BasicTicker
from bokeh.embed import components
from random import randint

#Create the Pathfinder Blueprint
bp = Blueprint(
    "pathfinder",
    __name__,
    template_folder="templates"
)

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

#Details JSON View
@bp.route("/populations/<population>")
@authenticate_request("pathfinder-browse")
def population_details(population):
    populations=[]
    for document in structure_collection().aggregate([
        {"$match":{"population":population}},
        {"$project":{
            "_id":0,
            "name":1,
            "population":1,
            "timestamp":1,
            "channels.name":1,
            "channels.type":1,
            "channels.unit":1
        }},
        {"$group":{
            "_id":"$population",
            "start":{"$first":"$timestamp"},
            "end":{"$last":"$timestamp"},
            "structures":{"$addToSet":"$name"},
            "channels":{"$addToSet":"$channels"}
        }},
        {"$project":{
            "_id":0,
            "name":"$_id",
            "start":1,
            "end":1,
            "structures":1,
            "channels":{
                "$reduce":{
                    "input":{
                        "$reduce":{
                            "input":"$channels",
                            "initialValue":[],
                            "in":{"$concatArrays":["$$value", "$$this"]}
                        }
                    },
                    "initialValue":[],
                    "in":{"$concatArrays":["$$value",{"$cond":[{"$in":["$$this","$$value"]},[],["$$this"]]}]}
                }
            }
        }},
        {"$limit":1}
    ]):
        populations.append(document)
    return jsonify(populations[0]) if len(populations) > 0 else jsonify()

#List View
@bp.route("/populations")
@authenticate_request("pathfinder-list")
def population_list(browse_endpoint="pathfinder.population_browse"):
    #Load All Populations
    populations=[]
    for document in structure_collection().aggregate([
        {"$group":{
            "_id":"$population",
            "start":{"$first":"$timestamp"},
            "end":{"$last":"$timestamp"},
            "structures":{"$addToSet":"$name"}
        }},
        {"$project":{"name":"$_id", "start":1, "end":1, "structures":1}},
        {"$sort":{"name":1}}
    ]):
        populations.append({
            "name":document["name"],
            "start":convert_nanoseconds(document["start"], "datetime"),
            "end":convert_nanoseconds(document["end"], "datetime"),
            "structures":document["structures"],
            "browse":url_for(browse_endpoint, population=document["name"])
        })
    #Render Template
    return render_template("list.html", populations=populations)

#Browse View
@bp.route("/populations/<population>/browse", methods=("GET", "POST"))
@authenticate_request("pathfinder-browse")
def population_browse(population):
    #Load All Populations
    populations=[]
    for document in structure_collection().aggregate([
        {"$group":{"_id":"$population"}},
        {"$sort":{"_id":1}}
    ]):
        populations.append(document["_id"])
    #Handle Request
    error, js, html, structures, channels=None, None, None, [], []
    if request.method == "POST":
        #Validate Inputs
        startDate = request.form["start-date"]
        startTime = request.form["start-time"]
        endDate = request.form["end-date"]
        endTime = request.form["end-time"]
        structures = request.form.getlist("structures")
        channels = request.form.getlist("channels")
        startDateParts = [int(part) for part in startDate.split("-")] if startDate else []
        startTimeParts = [int(part) for part in startTime.split(":")] if startTime else []
        endDateParts = [int(part) for part in endDate.split("-")] if endDate else []
        endTimeParts = [int(part) for part in endTime.split(":")] if endTime else []
        if len(startDateParts) != 3: error = "Start date not in yyyy-mm-dd format."
        elif len(startTimeParts) != 2: error = "Start time not in hh:mm format."
        elif len(endDateParts) != 3: error = "End date not in yyyy-mm-dd format."
        elif len(endTimeParts) != 2: error = "End time not in hh:mm format."
        #Process request if no errors
        if error is None:
            #Create Match and Project aggregate steps
            startTimestamp = datetime_to_nanoseconds_since_epoch(datetime(startDateParts[0], startDateParts[1], startDateParts[2], startTimeParts[0], startTimeParts[1], 0, 0))
            endTimestamp = datetime_to_nanoseconds_since_epoch(datetime(endDateParts[0], endDateParts[1], endDateParts[2], endTimeParts[0], endTimeParts[1], 59, 999999))
            match = {
                "population":population,
                "timestamp":{"$gte":startTimestamp, "$lte":endTimestamp}
            }
            if structures: match["name"] = {"$in":structures}
            if channels: match["channels.name"] = {"$in":channels}
            project = {
                "_id":0,
                "name":1,
                "timestamp":1
            }
            project["channels"] = {"$filter":{"input":"$channels", "as":"channel", "cond":{"$or":[{"$eq":["$$channel.name", channel]} for channel in channels]}}} if channels else 1
            #Query the database
            document_x, document_y, document_color={}, {}, {}
            for document in structure_collection().aggregate([
                {"$match":match},
                {"$project":project}
            ]):
                #Enumerate through channels
                for channel in document["channels"]:
                    if type(channel["value"]) == dict:
                        for key in channel["value"]:
                            name = "{structure_name} - {channel_name} ({key})".format(structure_name=document["name"], channel_name=channel["name"], key=key)
                            if name in document_x:
                                document_x[name].append(document["timestamp"])
                                document_y[name].append(channel["value"][key])
                            else:
                                document_x[name] = [document["timestamp"]]
                                document_y[name] = [channel["value"][key]]
                                document_color[name] = colors.named.__all__[randint(0, len(colors.named.__all__) - 1)]
                    elif type(channel["value"]) == int or type(channel["value"]) == float:
                        name = "{structure_name} - {channel_name}".format(structure_name=document["name"], channel_name=channel["name"])
                        if name in document_x:
                            document_x[name].append(document["timestamp"])
                            document_y[name].append(channel["value"])
                        else:
                            document_x[name] = [document["timestamp"]]
                            document_y[name] = [channel["value"]]
                            document_color[name] = colors.named.__all__[randint(0, len(colors.named.__all__) - 1)]
            #Create figure
            fig = figure(
                tools="pan,box_zoom,reset,save",
                output_backend="webgl",
                height=375,
                sizing_mode="scale_width",
                title="Population: {population} Structures: {structures} Channels: {channels}".format(
                    population=population,
                    structures=', '.join(structures) if structures else "All",
                    channels=', '.join(channels) if channels else "All"
                ),
                x_axis_label="Time",
            )
            fig.toolbar.logo=None
            fig.toolbar.autohide=True
            for line in document_x:
                fig.line(document_x[line], document_y[line], line_color=document_color[line], legend_label=line)

            fig.xaxis.formatter = CustomJSTickFormatter(code="""
                //DateTime Utilities
                function pad(number, padding) { return number.toString().padStart(padding, '0'); }
                function convertNanoseconds(nanoseconds) {
                    const milliseconds = Math.floor(nanoseconds / 1e6);
                    const remainderNanoseconds = nanoseconds - (milliseconds * 1e6);
                    return { milliseconds, remainderNanoseconds };
                }
                //Process Current Tick
                const {milliseconds, remainderNanoseconds} = convertNanoseconds(tick);         
                var date = new Date(milliseconds);
                var formattedSubSeconds = ((remainderNanoseconds > 0) ? "." + pad(date.getMilliseconds(), 3) + remainderNanoseconds.toString().padStart(6, '0') : (date.getMilliseconds() > 0) ? "." + pad(date.getMilliseconds(), 3) : '');
                return pad(date.getDate(), 2) + '/' + pad(date.getMonth() + 1, 2) + '/' + date.getFullYear() + " " + pad(date.getHours(), 2) + ':' + pad(date.getMinutes(), 2) + ':' + pad(date.getSeconds(), 2) + formattedSubSeconds;
            """)
            fig.xaxis.major_label_orientation = 3.14159264 / 2
            fig.xaxis.ticker = BasicTicker(desired_num_ticks=15)
            js, html=components(fig)
    #Render Template
    return render_template("browse.html", error=error, population=population, populations=populations, structures=structures, channels=channels, scripts=js, figure=html)
