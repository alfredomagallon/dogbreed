import os
import platform
import io
from datetime import datetime

import psycopg2
import numpy
import PIL

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from tensorflow import keras

from keras.applications.xception import preprocess_input
from keras.preprocessing.image import img_to_array
from keras.preprocessing.image import smart_resize

from flask import Flask, request, jsonify

# Dog breed identification service, provides an API endpoint where the picture is sent
# The predictions are sent as response

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

def bootstrap():

    print ('Showing versions ...')

    print('\tpython version:', platform.python_version())
    print('\tpsycopg2 version:', psycopg2.__version__)
    print('\tnumpy version:', numpy.__version__)
    print('\tpillow version:', PIL.__version__)
    print('\ttensorflow version:', keras.__version__)

    print('... versions shown.')

    start_time = datetime.now()
    print('Connecting to PostgreSQL database ...')

    conn = psycopg2.connect('host=' + str(os.environ.get("DOGBREEDDB_ADDR")) +' port=' + str(os.environ.get("DOGBREEDDB_PORT")) +
                            ' dbname=dogbreed' + 
                            ' user=' + str(os.environ.get("DOGBREEDDB_USER")) + ' password=' + str(os.environ.get("DOGBREEDDB_PASS")))

    end_time = datetime.now()
    print('... connected in {}.'.format(end_time-start_time))

    start_time = datetime.now()
    print('Counting pictures ...')

    sql= "SELECT COUNT(*) FROM pictures"
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    picture_qty = result[0][0]
    cursor.close()

    end_time = datetime.now()
    print('...', picture_qty, 'pictures counted in {}.'.format(end_time-start_time))

    start_time = datetime.now()
    print('Counting breeds ...')

    sql= "SELECT COUNT(*) FROM breeds"
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    breed_qty = result[0][0]
    cursor.close()

    end_time = datetime.now()
    print('...', breed_qty, 'breeds counted in {}.'.format(end_time-start_time))

    start_time = datetime.now()
    print('Retrieving breeds from PostgreSQL database ...')

    global breed_names

    breed_names = []
    sql= "SELECT name FROM breeds ORDER BY id"
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    index = 0
    for row in result:
        breed_names.append(row[0])
        index = index + 1
    cursor.close()

    end_time = datetime.now()
    print('... all breeds retrieved in {}.'.format(end_time-start_time))

    start_time = datetime.now()
    print('Initializing NumPy arrays for retrieving pictures (with breed) ...')

    train_pictures = numpy.empty((picture_qty, 400, 400, 3), dtype='uint8')
    train_breeds = numpy.empty((picture_qty), dtype='uint8')

    end_time = datetime.now()
    print('... model trained in {}.'.format(end_time-start_time))

    print('...', picture_qty * 2, 'arrays initialized in {}.'.format(end_time-start_time))

    start_time = datetime.now()
    print('Retrieving pictures with breed from PostgreSQL database ...')

    sql = "SELECT breed_id, breeds.name, pictures.id, pictures.name, picture FROM pictures INNER JOIN breeds ON pictures.breed_id = breeds.id ORDER BY random()"
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    end_time = datetime.now()
    print('... all pictures retrieved in {}.'.format(end_time-start_time))

    start_time = datetime.now()        
    print('Populating pictures with breed into NumPy arrays ...')

    index = 0
    for row in result:
        train_pictures[index] = img_to_array(PIL.Image.open(io.BytesIO(row[4])))
        train_breeds[index] = row[0]
        index = index + 1

    end_time = datetime.now()
    print('... pictures with breed populated in {}.'.format(end_time-start_time))

    start_time = datetime.now()
    print('Building the model ...')

    global model

    premodel = keras.applications.xception.Xception(input_shape=(400,400,3), include_top=False, weights='imagenet', pooling='avg')

    for layer in premodel.layers:
        layer.trainable = False

    model = keras.Sequential(
        [
            premodel,
            keras.layers.Dense(breed_qty, activation='softmax')
        ]
    )

    end_time = datetime.now()
    print('... model built in {}.'.format(end_time-start_time))

    start_time = datetime.now()
    print('Compiling the model ...')

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    end_time = datetime.now()
    print('... model compiled in {}.'.format(end_time-start_time))
    
    start_time = datetime.now()
    print('Training the model ...')

    epochs = 1
    batches = 300

    for e in range(epochs):
        print('Epoch', e+1, 'of', epochs)
        for b in range(batches):
            print('Batch', b+1, 'of', batches)
            x_batch = train_pictures[30*b:30*(b+1)-1]
            y_batch = train_breeds[30*b:30*(b+1)-1]
            x_batch = preprocess_input(x_batch)
            model.fit(x_batch, y_batch)

    end_time = datetime.now()
    print('... model trained in {}.'.format(end_time-start_time))

@app.route("/")
def main():
    print('Request received for /')
    return jsonify({'success': True})

@app.route("/identify", methods=["POST"])
def identification():
    print('Request received for /identify')
    file = request.files['image']
    img = PIL.Image.open(file.stream)
    array = img_to_array(img)
    resized_array = smart_resize(array, (400, 400))
    picture_to_identify = numpy.empty((1, 400, 400, 3), dtype='uint8')
    picture_to_identify[0] = resized_array
    predictions = model.predict(preprocess_input(picture_to_identify))
    results_dict = {k:v for k,v in zip(breed_names, predictions[0])}
    response = {'success': True}    
    response['predictions'] = []
    for breed, prob in results_dict.items():
        pred = {'breed': breed, 'probability': float(prob)}
        response['predictions'].append(pred)
    return jsonify(response)

if __name__ == "__main__":
    bootstrap()
    app.run(host='0.0.0.0', debug=False)
