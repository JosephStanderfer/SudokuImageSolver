import datetime
from flask import current_app
from google.cloud import storage
import six
from werkzeug import secure_filename
from werkzeug.exceptions import BadRequest

def _safe_filename(filename):
    filename = secure_filename(filename)
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
    basename, extension = filename.rsplit('.', 1)
    return "{0}-{1}.{2}".format(basename, date, extension)

def upload_file(file_stream, filename, content_type):
    filename = _safe_filename(filename)

    client = storage.Client(project=current_app.config['PROJECT_ID'])
    bucket = client.bucket(current_app.config['CLOUD_STORAGE_BUCKET'])
    blob = bucket.blob(filename)
    blob.upload_from_string(file_stream, content_type=content_type)
    url = blob.public_url

    if isinstance(url, six.binary_type):
        url = url.decode('utf-8')

    return url