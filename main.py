from flask import Flask, render_template, request
import pandas as pd
# import seaborn as sns
import numpy as np
import pickle
from sklearn.metrics import *

data = pd.read_csv("data/data.csv")
data = data.fillna(0)
#data = data[:100000]
print(data.index.size)

#drop_index = data[data['purchase'] > 100].index
#data.drop(drop_index,inplace=True)
print(data.index.size)
# data = data.drop_duplicates(subset='adset_id', keep='first')
#celebrity = pd.read_csv("data/data_celebrity.csv")
# print(data.index.size)
#drop_index = celebrity[celebrity['confidence'] < 85].index
#celebrity.drop(drop_index,inplace=True)
# celebrity = celebrity[['media_group_id','celebrity_name']]
#celebrity = celebrity.drop_duplicates(subset='media_group_id', keep='first')
# print(celebrity.size)
#data = pd.merge(data,celebrity,on="media_group_id",how="inn")
# print(data.size)
# data = data.join(celebrity, on="media_group_id")

# drop_index = data[data['click'] == 0].index
# data.drop(drop_index,inplace=True)

#celebrity = pd.read_csv("data/data_celebrity.csv")
#
#drop_index = celebrity[celebrity['confidence'] < 85].index
#celebrity.drop(drop_index, inplace=True)
#
#celebrity = celebrity.drop_duplicates(subset='media_group_id', keep='first')

#data = pd.merge(data, celebrity, on="media_group_id", how="left")
#data = data.fillna("no_celeb")

predicts = np.array(['impressions', 'video_view', 'clicks', 'install', 'purchase'])
targets = data[predicts]

features = data[[ 'publisher_platform', 'media_group_id', 'platform_position', 'spend', #'celebrity_name',
                 'account_age', 'countries', 'app_id', 'platform', 'user_os_version']]

categorical_data = data[[ 'app_id', 'media_group_id', 'publisher_platform', #'celebrity_name',
                         'platform_position','countries', 'platform','user_os_version']]

categorical_unique = []
categorical_label = []
continuous_label = ['spend', 'account_age']

for cat in categorical_data:
    categorical_unique.append(categorical_data[cat].unique())
    categorical_label.append(cat)
features = pd.get_dummies(data=features)  # one-hot
#features = pd.get_dummies(data=features, columns=["app_id"])  # one-hot
print(features.columns.size)
sample = pd.DataFrame([features.iloc[0]], columns=features.columns)
print(sample.columns.size)
for col in sample:
    sample[col] = 0


def linear(x_train, y_train):
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(x_train, y_train.values.ravel())

    return model


def lasso(x_train, y_train):
    from sklearn.linear_model import Lasso
    model = Lasso()
    model.fit(x_train, y_train.values.ravel())

    return model


def ridge(x_train, y_train):
    from sklearn.linear_model import Ridge
    model = Ridge(alpha=.5)
    model.fit(x_train, y_train.values.ravel())

    return model


def support_vector(x_train, y_train):
    from sklearn.svm import SVR
    model = SVR()
    model.fit(x_train, y_train.values.ravel())

    return model


def k_neighbours(x_train, y_train):
    from sklearn.neighbors import KNeighborsRegressor
    model = KNeighborsRegressor(n_neighbors=10)
    model.fit(x_train, y_train.values.ravel())

    return model


def random_forest(x_train, y_train):
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor()
    model.fit(x_train, y_train.values.ravel())

    return model


def ml_perceptron(x_train, y_train):
    from sklearn.neural_network import MLPRegressor
    model = MLPRegressor(max_iter=1000)
    model.fit(x_train, y_train.values.ravel())

    return model


def decision_tree(x_train, y_train):
    from sklearn.tree import DecisionTreeRegressor
    model = DecisionTreeRegressor()
    model.fit(x_train, y_train.values.ravel())

    return model


regressor = [linear, lasso, ridge, k_neighbours, random_forest, decision_tree, ml_perceptron] #,


def find_best():
    best_acc = [0, 0, 0, 0, 0]
    best_model_name = [0, 0, 0, 0, 0]
    best_model = 0

    for i in range(predicts.size):
        for reg in regressor:
            #for j in range(3):

            x = features
            y = targets[predicts[i]]

            from sklearn.model_selection import train_test_split
            x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.1)



            model = reg(x_train, y_train)
            acc = model.score(x_test, y_test)
            y_pred = (model.predict(x_test)).astype(int).clip(min=0)
            y_clip = np.array(y_test).clip(min=0.1)
            mape = mean_absolute_percentage_error(y_clip, y_pred)
            mae = median_absolute_error(y_test, y_pred)
            print('[' + predicts[i] + ']', reg.__name__, "acc: ", acc)
            print('[' + predicts[i] + ']', reg.__name__, "mape: ", mape)
            print('[' + predicts[i] + ']', reg.__name__, "mae: ", mae)

            if acc > best_acc[i]:
                best_acc[i] = acc
                best_model_name[i] = reg.__name__
                best_model = model

        print('[' + predicts[i] + ']'+' [' + best_model_name[i] + '] ' + '[best acc]: ', best_acc[i])
        with open('models/' + predicts[i] + ".pickle", 'wb') as file:
            pickle.dump(best_model, file)


def test_row(row):

    preds = []

    for i in range(5):
        with open('models/' + predicts[i] + ".pickle", 'rb') as file:
            model = pickle.load(file)
        preds.append(int(model.predict(row)))

    return preds


app = Flask(__name__)


@app.route('/')
def dropdown():
    return render_template('index.html',
                           drops=categorical_unique,
                           cat_lab=categorical_label,
                           cont_label=continuous_label)


@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'POST':
        new_sample = sample
        for i in categorical_label:
            new_sample[i + "_" + request.form.get(i)] = 1

        for i in continuous_label:
            if not request.form.get(i):
                new_sample[i] = 0
            else:
                new_sample[i] = request.form.get(i)

        predictions = test_row(new_sample)
        for i in range(len(predictions)):
            if predictions[i] < 0:
                predictions[i] = 0

        return render_template("index.html",
                               drops=categorical_unique,
                               cat_lab=categorical_label,
                               cont_label=continuous_label,
                               pred_label=predicts,
                               pred=predictions)
# else error

find_best()
app.run()
