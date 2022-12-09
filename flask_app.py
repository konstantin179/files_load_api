import os
from flask import Flask, request, abort, send_file, jsonify
from werkzeug.utils import secure_filename
from postgres import DB, db_connection_string
from pathlib import Path

FILES_FOLDER = './files_storage/files'
TEMPLATES_FOLDER = './files_storage/templates'
CLIENT_FILES_FOLDER = './files_storage/clients_files'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'txt'}

app = Flask(__name__)


@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_file_path(path):
    """Return path with new filename, if given file path already exists.
    'already_existed_name.txt' --> 'already_existed_name (1).txt'"""
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.isfile(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1
    return path


@app.route('/files/<filename>', methods=['POST'])
def upload_file(filename):
    """Upload a file to server.
    parameters:
      - name: filename
        in: path
        schema:
          type: string
        required: true
        description: "Filename with available file extensions: 'xlsx', 'xls', 'csv', 'txt'."
      - name: client_id
        in: query
        schema:
          type: integer
        required: true
      - name: file_group
        in: query
        schema:
          type: string
          default: "Прочее"
        required: false
        description: Name of file group"""
    client_id = request.args.get('client_id', type=int)
    if client_id is None:
        abort(400, description="Invalid request missing required parameter client_id")
    file_group = request.args.get('file_group', default="Прочее", type=str)
    # Check if the post request has the file data
    if not request.data:
        abort(400, description="No data was sent.")
    if not allowed_file(filename):
        abort(400, description=f"Bad file extension. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}.")
    filename = secure_filename(filename)
    client_dir_path = os.path.join(FILES_FOLDER, str(client_id))
    Path(client_dir_path).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(client_dir_path, filename)
    file_path = unique_file_path(file_path)
    filename = os.path.basename(file_path)
    with open(file_path, "wb") as f:
        f.write(request.data)
    with DB(db_connection_string) as db:
        db.insert_file_info_into_files_table(filename, client_id, file_group, file_path)
    return jsonify(message=f"File: {filename} successfully saved."), 201


@app.route("/files/")
def get_files_list():
    """Return list of dictionaries with info about saved files for client..
        parameters:
          - name: client_id
            in: query
            schema:
              type: integer
            required: true"""
    client_id = request.args.get('client_id', type=int)
    if client_id is None:
        abort(400, description="Invalid request missing required parameter client_id")
    with DB(db_connection_string) as db:
        files = db.get_list_of_files(client_id)
    return jsonify(files)


@app.route('/files/<file_id>')
def download_file(file_id):
    """Download the file by file_id.
    parameters:
      - name: file_id
        in: path
        schema:
          type: integer
        required: true"""
    with DB(db_connection_string) as db:
        file_path = db.get_file_path_from_files_table(file_id)
    if not file_path:
        abort(404, description=f"File with id {file_id} does not exist.")
    return send_file(file_path)


@app.route('/templates/<filename>', methods=['POST'])
def upload_template(filename):
    """Upload a template to server.
    parameters:
      - name: filename
        in: path
        schema:
          type: string
        required: true
        description: "Filename with available file extensions: 'xlsx', 'xls', 'csv', 'txt'."
      - name: file_group
        in: query
        schema:
          type: string
          default: "Прочее"
        required: false
        description: Name of file group."""
    file_group = request.args.get('file_group', default="Прочее", type=str)
    # Check if the post request has the file data
    if not request.data:
        abort(400, description="No data was sent.")
    if not allowed_file(filename):
        abort(400, description=f"Bad file extension. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}.")
    filename = secure_filename(filename)
    file_path = os.path.join(TEMPLATES_FOLDER, filename)
    if os.path.isfile(file_path):
        abort(400, description=f"Template {filename} already exists.")
    with open(file_path, "wb") as f:
        f.write(request.data)
    with DB(db_connection_string) as db:
        db.insert_file_info_into_templates_table(filename, file_group, file_path)
    return jsonify(message=f"Template: {filename} successfully saved."), 201


@app.route("/templates/")
def get_templates_list():
    """Return list of dictionaries with info about available templates."""
    with DB(db_connection_string) as db:
        files = db.get_list_of_templates()
    return jsonify(files)


@app.route('/templates/<file_id>')
def download_template(file_id):
    """Download the template by file_id.
    parameters:
      - name: file_id
        in: path
        schema:
          type: integer
        required: true"""
    with DB(db_connection_string) as db:
        file_path = db.get_file_path_from_templates_table(file_id)
    if not file_path:
        abort(404, description=f"Template with id {file_id} does not exist.")
    return send_file(file_path)


@app.route('/client_files/<filename>', methods=['POST'])
def upload_client_file(filename):
    """Upload a client file to server.
    parameters:
      - name: filename
        in: path
        schema:
          type: string
        required: true
        description: "Filename with available file extensions: 'xlsx', 'xls', 'csv', 'txt'."
      - name: client_id
        in: query
        schema:
          type: integer
        required: true
      - name: file_group
        in: query
        schema:
          type: string
          default: "Прочее"
        required: false
        description: Name of file group"""
    client_id = request.args.get('client_id', type=int)
    if client_id is None:
        abort(400, description="Invalid request missing required parameter client_id")
    file_group = request.args.get('file_group', default="Прочее", type=str)
    # Check if the post request has the file data
    if not request.data:
        abort(400, description="No data was sent.")
    if not allowed_file(filename):
        abort(400, description=f"Bad file extension. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}.")
    filename = secure_filename(filename)
    client_dir_path = os.path.join(CLIENT_FILES_FOLDER, str(client_id))
    Path(client_dir_path).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(client_dir_path, filename)
    file_path = unique_file_path(file_path)
    filename = os.path.basename(file_path)
    with open(file_path, "wb") as f:
        f.write(request.data)
    with DB(db_connection_string) as db:
        db.insert_file_info_into_client_files_table(filename, client_id, file_group, file_path)
    return jsonify(message=f"Client file: {filename} successfully saved."), 201


@app.route("/client_files/")
def get_client_files_list():
    """Return list of dictionaries with info about saved client files..
    parameters:
      - name: client_id
        in: query
        schema:
          type: integer
        required: true"""
    client_id = request.args.get('client_id', type=int)
    if client_id is None:
        abort(400, description="Invalid request missing required parameter client_id")
    with DB(db_connection_string) as db:
        files = db.get_list_of_client_files(client_id)
    return jsonify(files)


@app.route('/client_files/<file_id>')
def download_client_file(file_id):
    """Download the client file by file_id..
    parameters:
      - name: file_id
        in: path
        schema:
          type: integer
        required: true
        description: client file ID."""
    with DB(db_connection_string) as db:
        file_path = db.get_file_path_from_client_files_table(file_id)
    if not file_path:
        abort(404, description=f"Client file with id {file_id} does not exist.")
    return send_file(file_path)


if __name__ == '__main__':
    app.run(debug=True)
