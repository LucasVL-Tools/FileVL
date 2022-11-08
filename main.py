#!/usr/bin/env python3
from flask import Flask, request, render_template, redirect, abort, send_from_directory, send_file
import logging, os, random, sys
from waitress import serve
from werkzeug.utils import secure_filename
from config import (host, port, title, domain, unix_socket, captcha_site_key, captcha_secret_key, url_length, url_letters, enable_captcha, max_files)

# Logging stuff for the waitress WSGI server
logging.basicConfig()
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

# Starts the auto-deleter, done by forking the process and checking if the process is a parent or child. if process is child, run auto delete. if process is parent, run iapp.
#n = os.fork()
#if n > 0:
#    import auto_delete
#    while True: pass
#else: print("App started!")

app = Flask(__name__)
app.config.update(
    XCAPTCHA_SITE_KEY = captcha_site_key,
    XCAPTCHA_SECRET_KEY = captcha_secret_key
)
if enable_captcha:
    from flask_xcaptcha import XCaptcha
    xcaptcha = XCaptcha(app=app, theme="dark")

# Code for serving home page
@app.route("/", methods=['GET'])
def home():
    filecount = request.args.get("filecount")
    if filecount:
        filecount = int(filecount)
        filecount += 1
    else: filecount = 1
    if filecount >= max_files: filecount = max_files

    return render_template("index.html", domain=domain, title=title, filecount=filecount)

@app.route("/output", methods=['POST'])
def upload():
    if enable_captcha:
        if not xcaptcha.verify():
            return render_template("errors.html", error="Captcha Failed, please complete the captcha and try again.", title=title, domain=domain)
    while True:
        url = ""
        for i in range(url_length):
            url += random.choice(url_letters)
        taken_urls = os.listdir("./files")
        if url not in taken_urls:
            break

    os.mkdir(f"./files/{url}")
    
    files = []
    filecount = int(request.form.get("filecount"))
    if filecount >= max_files: filecount = max_files
    empty = True
    for i in range(filecount):
        file = request.files[f"file{i}"]
        filename = secure_filename(file.filename)
        if filename:
            file.save(f"./files/{url}/{filename}")
            empty = False
    if not empty:
        return render_template("output.html", url=url, title=title, domain=domain)
    else:
        os.rmdir(f"./files/{url}")
        return render_template("errors.html", title=title, domain=domain, error="No files provided, please upload a file.")

@app.route("/f/<url>", methods=['GET'])
def fileindex(url):
    files = os.listdir(f"./files/{url}")

    if len(files) == 1:
        return redirect(f"/f/{url}/{files[0]}", 302)

    filetype = []
    images = 0
    for file in files:
        ext = file[file.rfind("."):]
        if ext.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".svg", ".gif", ".webp", ".tiff"]:
            filetype.append("image")
            images += 1
        else: 
            filetype.append(False)
    if images >= 4: filetype = False

    return render_template("files.html", files=files, url=url, filetype=filetype)

@app.route("/f/<url>/<file>")
def downloadfile(url, file):
    if request.args.get("play"):
        return send_file(f"files/{url}/{file}")
    return send_from_directory("files", f"{url}/{file}", as_attachment = True)

###############
# ERROR PAGES #
###############

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', domain=domain, title="404 - page not found"), 404

# checks for unix socket or host in config file and runs waitress accordingly. 

#from werkzeug.middleware.profiler import ProfilerMiddleware
#app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[5], profile_dir="./profile")
app.run(debug = True)
"""

if host:
    serve(app, host=host, port=port)
elif unix_socket:
    serve(app, unix_socket=unix_socket, unix_socket_perms="777")
else: print("Please specify a host or unix socket (you probably just want host to be set to 0.0.0.0)")
"""
