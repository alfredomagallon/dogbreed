import platform
import os
from flask import Flask, flash, render_template, request, redirect
import requests
import PIL
from PIL import Image
import io
import base64
import psycopg2
from datetime import datetime

# Simple UI for the dog breed identification service
# Uses the PostgreSQL database to store history

history = 20

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.secret_key="app supersecret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def bootstrap():

    print ('Showing versions ...')

    print('\tpython version:', platform.python_version())
    print('\tpsycopg2 version:', psycopg2.__version__)
    print('\tpillow version:', PIL.__version__)

    print('... versions shown.')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def database_process(file, breed, success):

    start_time = datetime.now()
    print('Connecting to PostgreSQL database ...')

    conn = psycopg2.connect('host=' + str(os.environ.get("DOGBREEDDB_ADDR")) +' port=' + str(os.environ.get("DOGBREEDDB_PORT")) +
                            ' dbname=dogbreed' + 
                            ' user=' + str(os.environ.get("DOGBREEDDB_USER")) + ' password=' + str(os.environ.get("DOGBREEDDB_PASS")))

    end_time = datetime.now()
    print('... connected in {}.'.format(end_time-start_time))

    start_time = datetime.now()
    print('Insert record into history ...')

    sql = "INSERT INTO history (picture, breed, success) VALUES (%s, %s, %s)"
    cursor = conn.cursor()
    cursor.execute(sql, (file.read(), breed, success))
    cursor.close()
    conn.commit()

    end_time = datetime.now()
    print('... inserted in {}.'.format(end_time-start_time))

    start_time = datetime.now()
    print('Fetching latest attempts ...')

    sql = 'SELECT picture, breed, success FROM history ORDER BY id DESC limit ' + str(history)
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    
    end_time = datetime.now()
    print('... fetched in {}.'.format(end_time-start_time))

    cursor.close()
    conn.close()

    return result

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # If the post comes from the result template, display final template
        if request.form['submit_button'] == '  Yes  ':
            history = database_process(io.BytesIO(base64.b64decode(request.form['image'])),request.form['breed'],True)
            history_picture = []
            history_breed = []
            history_success = []
            for attempt in history:
                history_picture.append(base64.b64encode(io.BytesIO(attempt[0]).getvalue()).decode('utf-8'))
                history_breed.append(attempt[1])
                history_success.append(attempt[2])
            ready_history = [list(attempt) for attempt in zip(history_picture, history_breed, history_success)]
            # Show latest attempts
            return render_template('final.html', history=ready_history)
        else:
            if request.form['submit_button'] == '  No  ':
                history = database_process(io.BytesIO(base64.b64decode(request.form['image'])),request.form['breed'],False)
                index = 0
                history_picture = []
                history_breed = []
                history_success = []
                for attempt in history:
                    history_picture.append(base64.b64encode(io.BytesIO(attempt[0]).getvalue()).decode('utf-8'))
                    history_breed.append(attempt[1])
                    history_success.append(attempt[2])
                ready_history = [list(attempt) for attempt in zip(history_picture, history_breed, history_success)]
                # Show latest attempts
                return render_template('final.html', history=ready_history)
            else:
                # if the post comes from the index template, process file
                if 'file' not in request.files:
                    flash('No file part')
                file = request.files['file']
                if file.filename == '':
                    flash('No selected file')
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    url = 'http://' + str(os.environ.get("DOGBREEDSVC_ADDR")) + ':' + str(os.environ.get("DOGBREEDSVC_PORT")) + '/identify'
                    my_img = {'image': file}
                    r = requests.post(url, files=my_img)
                    max_prob = 0
                    for i in range(len(r.json()['predictions'])):
                        if r.json()['predictions'][i]['probability']>max_prob:
                            max_prob = r.json()['predictions'][i]['probability']
                            predicted_breed = r.json()['predictions'][i]['breed']                    
                    picture = Image.open(file.stream)
                    picture.thumbnail((400,400))
                    imgbytes = io.BytesIO()
                    picture.save(imgbytes, "JPEG")
                    encoded_picture = base64.b64encode(imgbytes.getvalue())
                    if predicted_breed[0]=='A':
                        connword = 'an'
                    else:
                        connword = 'a'
                    return render_template('result.html', picture=encoded_picture.decode('utf-8'), breed=predicted_breed, connword = connword)
    else:
        # if it's a get, show main page
        return render_template('index.html')

if __name__ == "__main__":
    bootstrap()
    ssl_context=(os.environ.get("DOGBREEDUI_CERT"), os.environ.get("DOGBREEDUI_KEY"))
    print(ssl_context)
    app.run(host='0.0.0.0', port='443', ssl_context=ssl_context, debug=False)
