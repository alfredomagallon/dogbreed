import glob,os
from datetime import datetime

from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from keras.preprocessing.image import smart_resize
from keras.preprocessing.image import save_img

# Resize all the pictures in the tree, saving them with a different name

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

start_time = datetime.now()
print("Scanning images folder ...")

for dirpath, dirnames, filenames in sorted(os.walk("./images")):
    for dirname in sorted(dirnames):
        index = 1
        print("Processing", dirname, "...")
        files = glob.glob('./images/' + dirname + '/*_resized.jpg')
        for file in files:
            os.remove(file)
        for dirpath, dirnames, filenames in sorted(os.walk("./images/" + dirname)):
            for filename in sorted(filenames):
                if filename != ".DS_Store":
                    file = os.path.join(dirpath, filename)
                    img = load_img(file)
                    array = img_to_array(img)
                    resized_array = smart_resize(array, (400, 400))
                    print("Saving resized", file, "to", os.path.join(dirpath, dirname + "_" + str(index).zfill(3) + "_resized.jpg"))
                    save_img(os.path.join(dirpath, dirname + "_" + str(index).zfill(3) + "_resized.jpg"), resized_array)
                    index = index + 1

end_time = datetime.now()
print('... preparation complete in {}.'.format(end_time-start_time))