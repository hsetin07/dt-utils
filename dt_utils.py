from flask import Flask, render_template, make_response
from dt_procs import dt_get_outdated_procs, dt_get_host_units, dt_get_events, dt_ocp_mem_usage

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/proc_req_restart/<string:format>")
def proc_req_restart(format):
    v = dt_get_outdated_procs()
    if format == "csv":
        s = ""
        for row in v:
            s += "%s\n" % ", ".join(row)
        output = make_response(s)
        output.headers["Content-Disposition"] = "attachment; filename=proc_req_restart.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    # else html
    return render_template('proc_req_restart_out.html', head=v[0], lst=v[1:])
    
    dt_get_host_units

@app.route("/host_units/<string:format>")
def host_units(format):
    v = dt_get_host_units()
    if format == "csv":
        s = ""
        for row in v:
            s += "%s\n" % ", ".join(row)
        output = make_response(s)
        output.headers["Content-Disposition"] = "attachment; filename=host_units.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    # else html
    return render_template('host_units.html', head=v[0], lst=v[1:])

@app.route("/events/<string:format>")
def events(format):
    v = dt_get_events()
    if format == "csv":
        s = ""
        for row in v:
            s += "%s\n" % ", ".join(row)
        output = make_response(s)
        output.headers["Content-Disposition"] = "attachment; filename=events.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    # else html
    return render_template('events.html', head=v[0], lst=v[1:])

@app.route("/ocp_mem/<string:format>")
def ocp_mem(format):
    v = dt_ocp_mem_usage()
    if format == "csv":
        s = ""
        for row in v:
            s += "%s\n" % ", ".join(row)
        output = make_response(s)
        output.headers["Content-Disposition"] = "attachment; filename=ocp_mem.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    # else html
    return render_template('ocp_mem.html', head=v[0], lst=v[1:])
