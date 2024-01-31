from flask import Blueprint

#Create the layout Blueprint
bp = Blueprint(
    "layout",
    __name__,
    static_folder = "static",
    template_folder = "templates"
)