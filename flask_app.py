import os
import logging
import pandas as pd
import requests
import json
from flask import Flask, request, abort, send_file, jsonify, render_template
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from postgres import DB, db_connection_string
from pathlib import Path
from time import localtime, strftime
from flask_cors import CORS

FILES_FOLDER = './files_storage/client_report_files'
TEMPLATES_FOLDER = './files_storage/file_templates'
CLIENT_FILES_FOLDER = './files_storage/clients_files'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
ALLOWED_METHODS = {'/graphs/cart_to_order_conversion', '/graphs/costs_cpo', '/graphs/costs_cpm_cpo',
                   '/graphs/impressions_to_cart_conversion', '/graphs/hits_view', '/graphs/org_traffic',
                   '/graphs/average_check', '/graphs/ddr', '/graphs/adv_view_all', '/graphs/costs_cpm',
                   '/graphs/full', '/graphs/impressions_to_order_conversion', '/graphs/share_of_paid_impressions',
                   '/graphs/adv_view_all_org_traffic', '/graphs/ordered', '/graphs/revenue', '/graphs/adv_sum_all'}

app = Flask(__name__)
CORS(app)

# Add file handler to app.logger
fh = logging.FileHandler(filename='files_load_api.log')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s - %(funcName)s - %(message)s')
fh.setFormatter(formatter)
app.logger.addHandler(fh)

app.logger.setLevel(logging.INFO)


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_file_path(path):
    """Return path with new filename, if given file path already exists.
    'already_existed_name.csv' --> 'already_existed_name (1).csv'"""
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.isfile(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1
    return path


@app.route('/docs')
def get_docs():
    return render_template('swaggerui.html')


@app.route('/client_report_files/<filename>', methods=['POST'])
def upload_file(filename):
    """Upload a client report file to server.
    parameters:
      - name: filename
        in: path
        schema:
          type: string
        required: true
        description: "Filename with available file extensions: 'xlsx', 'xls', 'csv'."
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
        app.logger.warning("400 Invalid request missing required parameter client_id")
        abort(400, description="Invalid request missing required parameter client_id")
    file_group = request.args.get('file_group', default="Прочее", type=str)
    # Check if the post request has the file data
    if not request.data:
        app.logger.warning("400 No data was sent.")
        abort(400, description=f"400 Client_id {client_id} - {filename} - No data was sent.")
    if not allowed_file(filename):
        app.logger.warning(f"400 Client_id {client_id} - {filename} - Bad file extension.")
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
        db.insert_file_info_into_client_report_files_table(filename, client_id, file_group, file_path)
    app.logger.info(f"201 Client_id {client_id} - File: {filename} successfully saved.")
    return jsonify(message=f"File: {filename} successfully saved."), 201


@app.route("/client_report_files/")
def get_client_report_files_list():
    """Return list of dictionaries with info about saved files for client..
        parameters:
          - name: client_id
            in: query
            schema:
              type: integer
            required: true"""
    client_id = request.args.get('client_id', type=int)
    if client_id is None:
        app.logger.warning("400 Invalid request missing required parameter client_id")
        abort(400, description="Invalid request missing required parameter client_id")
    with DB(db_connection_string) as db:
        files = db.get_list_of_client_report_files(client_id)
    app.logger.info(f"200 Client_id {client_id} - Сlient report files info list was sent.")
    return jsonify(files)


@app.route('/client_report_files/<file_id>', methods=['GET', 'DELETE'])
def download_or_delete_client_report_file(file_id):
    """Download or delete the client report file by file_id.
      get:
        parameters:
          - name: file_id
            in: path
            schema:
              type: integer
            required: true
      delete:
        parameters:
          - name: file_id
            in: path
            schema:
              type: integer
            required: true
          - name: secret_key
            in: query
            schema:
              type: string
            required: true"""
    with DB(db_connection_string) as db:
        file_path = db.get_file_path_from_client_report_files_table(file_id)
    if request.method == 'GET':
        if not file_path:
            app.logger.warning(f"404 File with id {file_id} does not exist.")
            abort(404, description=f"File with id {file_id} does not exist.")
        app.logger.info(f"200 File with id {file_id} was sent.")
        return send_file(file_path)

    if request.method == 'DELETE':
        secret_key = request.args.get('secret_key', type=str)
        if secret_key == os.getenv("DELETE_KEY"):
            if not file_path:
                app.logger.info(f"File with id {file_id} is already deleted.")
                return jsonify(message=f"File with id {file_id} is already deleted."), 200
            os.remove(file_path)
            with DB(db_connection_string) as db:
                db.delete_from_table('client_report_files', file_id)
            return jsonify(message=f"File with id {file_id} was deleted."), 200
        else:
            app.logger.warning("400 Invalid request missing required parameter secret_key")
            abort(400, description="Invalid request missing required parameter secret_key")


@app.route('/templates/<filename>', methods=['POST'])
def upload_template(filename):
    """Upload a template to server.
    parameters:
      - name: filename
        in: path
        schema:
          type: string
        required: true
        description: "Filename with available file extensions: 'xlsx', 'xls', 'csv'."
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
        app.logger.warning("400 No data was sent.")
        abort(400, description="No data was sent.")
    if not allowed_file(filename):
        app.logger.warning(f"400 Filename: {filename} - Bad file extension.")
        abort(400, description=f"Bad file extension. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}.")
    filename = secure_filename(filename)
    file_path = os.path.join(TEMPLATES_FOLDER, filename)
    if os.path.isfile(file_path):
        app.logger.warning(f"400 Template {filename} already exists.")
        abort(400, description=f"Template {filename} already exists.")
    with open(file_path, "wb") as f:
        f.write(request.data)
    with DB(db_connection_string) as db:
        db.insert_file_info_into_templates_table(filename, file_group, file_path)
    app.logger.info(f"Template: {filename} successfully saved.")
    return jsonify(message=f"Template: {filename} successfully saved."), 201


@app.route("/templates/")
def get_templates_list():
    """Return list of dictionaries with info about available templates."""
    with DB(db_connection_string) as db:
        files = db.get_list_of_templates()
    app.logger.info(f"200 Templates info list was sent.")
    return jsonify(files)


@app.route('/templates/<file_id>', methods=['GET', 'DELETE'])
def download_or_delete_template(file_id):
    """Download or delete the template by file_id.
      get:
        parameters:
          - name: file_id
            in: path
            schema:
              type: integer
            required: true
      delete:
        parameters:
          - name: file_id
            in: path
            schema:
              type: integer
            required: true
          - name: secret_key
            in: query
            schema:
              type: string
            required: true"""
    with DB(db_connection_string) as db:
        file_path = db.get_file_path_from_templates_table(file_id)
    if request.method == 'GET':
        if not file_path:
            app.logger.warning(f"404 Template with id {file_id} does not exist.")
            abort(404, description=f"Template with id {file_id} does not exist.")
        app.logger.info(f"200 File with id {file_id} was sent.")
        return send_file(file_path)
    if request.method == 'DELETE':
        secret_key = request.args.get('secret_key', type=str)
        if secret_key == os.getenv("DELETE_KEY"):
            if not file_path:
                app.logger.info(f"Template with id {file_id} is already deleted.")
                return jsonify(message=f"Template with id {file_id} is already deleted."), 200
            os.remove(file_path)
            with DB(db_connection_string) as db:
                db.delete_from_table('file_templates', file_id)
            return jsonify(message=f"Template with id {file_id} was deleted."), 200
        else:
            app.logger.warning("400 Invalid request missing required parameter secret_key")
            abort(400, description="Invalid request missing required parameter secret_key")


@app.route('/client_files/<filename>', methods=['POST'])
def upload_client_file(filename):
    """Upload a client file to server.
    parameters:
      - name: filename
        in: path
        schema:
          type: string
        required: true
        description: "Filename with available file extensions: 'xlsx', 'xls', 'csv'."
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
        app.logger.warning("400 Invalid request missing required parameter client_id")
        abort(400, description="Invalid request missing required parameter client_id")
    file_group = request.args.get('file_group', default="Прочее", type=str)
    # Check if the post request has the file data
    if not request.data:
        app.logger.warning("400 No data was sent.")
        abort(400, description="No data was sent.")
    if not allowed_file(filename):
        app.logger.warning(f"400 Client_id {client_id} - {filename} - Bad file extension.")
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
    app.logger.info(f"201 Client_id {client_id} - Client file: {filename} successfully saved.")
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
        app.logger.warning("400 Invalid request missing required parameter client_id")
        abort(400, description="Invalid request missing required parameter client_id")
    with DB(db_connection_string) as db:
        files = db.get_list_of_client_files(client_id)
    app.logger.info(f"200 Client_id {client_id} - Client files info list was sent.")
    return jsonify(files)


@app.route('/client_files/<file_id>', methods=['GET', 'DELETE'])
def download_or_delete_client_file(file_id):
    """Download or delete the client file by file_id.
      get:
        parameters:
          - name: file_id
            in: path
            schema:
              type: integer
            required: true
            description: client file ID
      delete:
        parameters:
          - name: file_id
            in: path
            schema:
              type: integer
            required: true
          - name: secret_key
            in: query
            schema:
              type: string
            required: true"""
    with DB(db_connection_string) as db:
        file_path = db.get_file_path_from_client_files_table(file_id)
    if request.method == 'GET':
        if not file_path:
            app.logger.warning(f"404 File with id {file_id} does not exist.")
            abort(404, description=f"Client file with id {file_id} does not exist.")
        app.logger.info(f"200 Client file with id {file_id} was sent.")
        return send_file(file_path)
    if request.method == 'DELETE':
        secret_key = request.args.get('secret_key', type=str)
        if secret_key == os.getenv("DELETE_KEY"):
            if not file_path:
                app.logger.info(f"Client file with id {file_id} is already deleted.")
                return jsonify(message=f"Client file with id {file_id} is already deleted."), 200
            os.remove(file_path)
            with DB(db_connection_string) as db:
                db.delete_from_table('client_files', file_id)
            return jsonify(message=f"Client file with id {file_id} was deleted."), 200
        else:
            app.logger.warning("400 Invalid request missing required parameter secret_key")
            abort(400, description="Invalid request missing required parameter secret_key")


@app.route('/report', methods=['POST'])
def get_report():
    """Return report for client.
        parameters:
          - name: method
            in: query
            schema:
              type: string
            required: true
            example: "/dashboard_sales_filter/client"
          - name: client_id
            in: query
            schema:
              type: integer
            required: true"""
    client_id = request.args.get('client_id', type=int)
    if client_id is None:
        app.logger.warning("400 Invalid request missing required parameter client_id")
        abort(400, description="Invalid request missing required parameter client_id")
    method = request.args.get('method', type=str)
    if method is None:
        app.logger.warning("400 Invalid request missing required parameter method")
        abort(400, description="Invalid request missing required parameter method")
    if method not in ALLOWED_METHODS:
        app.logger.warning(f"400 Method {method} is not allowed")
        abort(400, description=f"400 Method {method} is not allowed. Allowed methods: {', '.join(ALLOWED_METHODS)}")

    result = None
    url = "https://apps1.ecomru.ru:4450/api/v1" + method
    json_data = request.json
    print(type(json_data))
    print(json_data)
    try:
        response = requests.post(url, json=json_data)
        if response.status_code in {400, 404, 422, 500}:
            abort(response.status_code, description=repr(response.json()))
        result = response.json()
    except requests.exceptions.RequestException as e:
        app.logger.warning(repr(e))
        abort(404, description=repr(e))

    print(result)
    if type(result) is list:
        df = pd.DataFrame.from_records(result)
    elif type(result) is dict:
        values = list(result.values())
        if type(values[0]) is list:
            df = pd.DataFrame.from_dict(result)
        else:
            df = pd.DataFrame.from_records([result])
    else:
        app.logger.error(f"Unable to convert result to dataframe; result type: {type(result)}.")
        abort(500, description="Unable to convert result to dataframe.")

    method_name = method[1:].replace('/', ' ')
    filename = f"{method_name} {strftime('%d-%m-%y %H:%M', localtime())}.xlsx"
    client_dir_path = os.path.join(FILES_FOLDER, str(client_id))
    Path(client_dir_path).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(client_dir_path, filename)
    file_path = unique_file_path(file_path)
    filename = os.path.basename(file_path)
    file_group = method_name  # ????????????????????
    df.to_excel(file_path)
    with DB(db_connection_string) as db:
        db.insert_file_info_into_client_report_files_table(filename, client_id, file_group, file_path)
    app.logger.info(f"Client_id {client_id} - File: {filename} successfully saved.")
    app.logger.info(f"200 Client_id {client_id} - File: {filename} was sent.")
    return send_file(file_path)


# @app.route('/')
# def excel_to_json():
#     df = pd.read_excel('example.xlsx', dtype=str, header=None)
#     first_value = df.iat[0, 0]
#     if (re.match(r"артикул*", first_value, re.IGNORECASE) or
#             re.match(r"artic*", first_value, re.IGNORECASE)):
#         df.drop(df.index[0], inplace=True)
#     values = df[0].tolist()
#     result = {'vendor_code': values}
#     return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
