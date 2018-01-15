# coding: utf-8

import numpy as np
import pandas as pd

from collections import Counter

from utils.data_utils import label_transform, PredictFileSequence
from settings import train_path, test_path, submissions_path, weights_path
from utils.file_utils import get_train_df, get_test_df
from models import CNN1, CNNConv4, CNNConv10
from kaggle.utils import create_logger

from PIL import Image

Image.MAX_IMAGE_PIXELS = 1000000000

logger = create_logger('submit')

if __name__ == '__main__':

    batch_size = 16
    crop_shape = 64

    train_df = get_train_df(train_path, use_crop=False, use_original=True)
    logger.info('train.shape={}'.format(train_df.shape))

    y, label_index = label_transform(train_df['camera'].values)
    y = np.array(y)

    model = CNNConv10.model(len(label_index), batch_size, crop_shape)

    model_version = 'cnn_conv10-20180114-1632.latest-20'

    file_path = "{}/{}.hdf5".format(weights_path, model_version)
    model.load_weights(file_path)

    s_name = '{}/submission-{}.csv'.format(submissions_path, model_version)

    test_df = get_test_df(test_path)

    predictions = []

    for i in range(20):
        X_test = PredictFileSequence(test_df['path'].values, batch_size, crop_shape)
        predicts = model.predict_generator(X_test, use_multiprocessing=True, workers=10)

        predicts = np.argmax(predicts, axis=1)
        predicts = [label_index[p] for p in predicts]
        assert test_df.shape[0] == len(predicts), '{} != {}'.format(test_df.shape[0], len(predicts))
        predictions.append(predicts)

    final_predicts = []

    for row in zip(*predictions):
        counter = Counter(row)
        final_predicts.append(counter.most_common(1)[0][0])

    df = pd.DataFrame(columns=['fname', 'camera'])
    df['fname'] = test_df['fname'].values
    df['camera'] = final_predicts

    df.to_csv(s_name, index=False)

    logger.info('save to {}'.format(s_name))