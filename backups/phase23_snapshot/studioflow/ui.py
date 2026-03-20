from flask import Blueprint, render_template

ui = Blueprint("ui", __name__, template_folder="templates")


@ui.get("/ui/")
def dashboard():
    return render_template("ui/dashboard.html")


@ui.get("/ui/workflow")
def workflow():
    return render_template("ui/workflow.html")


@ui.get("/ui/reviews")
def reviews():
    return render_template("ui/reviews.html")


@ui.get("/ui/projects")
def projects():
    return render_template("ui/projects.html")


@ui.get("/ui/projects/new")
def projects_new():
    return render_template("ui/projects_new.html")


@ui.get("/ui/projects/<project_id>")
def project_detail(project_id):
    return render_template("ui/project_detail.html", project_id=project_id)
