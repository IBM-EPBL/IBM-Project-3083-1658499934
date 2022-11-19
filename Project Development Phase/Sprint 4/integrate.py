import pandas as pd
import numpy as np
from flask import Flask,render_template,Response,request
import pickle
from sklearn.preprocessing import LabelEncoder
import requests

API_KEY = "y9fOFST6bMUm-ugNLk5iQoRH9dK4auxmxI6Wj61jiF5R"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
 API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}

app = Flask(__name__,template_folder="template")
filename = 'resale_model.sav'
model_rand = pickle.load(open(filename,'rb'))

@app.route('/')
def index():
	return render_template('home.html')

@app.route('/predict')
def predict():
	return render_template('prediction.html')

@app.route('/y_predict',methods=['GET','POST'])
def y_predict():
	regyear = request.form.get('regyear')
	powerps = request.form.get('powerps')
	kms= request.form.get('kms')
	regmonth = request.form.get('regmonth')
	gearbox = request.form.get('gearbox')
	damage = request.form.get('dam')
	model  = request.form.get('model_type')
	brand = request.form.get('brand')
	fuelType = request.form.get('fuel')
	vehicletype= request.form.get('vehicletype')
	new_row = {'yearOfRegistration':regyear,'powerPS':powerps,'kilometer':kms,'monthOfRegistration':regmonth,'gearbox':gearbox,'notRepairedDamage':damage,'model':model,'brand':brand,'fuelType':fuelType,'vehicleType':vehicletype}

	print(new_row)
	new_df = pd.DataFrame(columns=['yearOfRegistration','vehicleType','gearbox','powerPS','model','kilometer','monthOfRegistration','fuelType','brand','notRepairedDamage'])
	new_df = new_df.append(new_row,ignore_index=True)
	labels = ['gearbox','notRepairedDamage','model','brand','fuelType','vehicleType']
	mapper = {}
	for i in labels:
		mapper[i] = LabelEncoder()
		mapper[i].classes_ = np.load(str('classes'+i+'.npy'),allow_pickle=True)
		tr = mapper[i].fit_transform(new_df[i])
		new_df.loc[:,i+'_Labels'] = pd.Series(tr,index=new_df.index)
	labeled = new_df[ ['yearOfRegistration','powerPS','kilometer','monthOfRegistration'] + [x+"_Labels" for x in labels]]

	X= labeled.values.tolist()
	print(X)
	payload_scoring = {"input_data": [{"fields": [['yearOfRegistration','powerPS','kilometer','monthOfRegistration''gearbox_labels', 'notRepairedDamage_labels', 'model_labels','brand_labels', 'fuelType_labels', 'vehicleType_labels']], "values": X}]}

	response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/a5525aa6-c9c6-4baf-acd7-3715c01d4eeb/predictions?version=2022-11-18', json=payload_scoring, headers={'Authorization': 'Bearer ' + mltoken})
	predictions = response_scoring.json()
	print(predictions)
	pred = predictions['predictions'][0]['values'][0][0]
	print("print",pred)
	return render_template('value.html',ypred=pred)

if __name__ == '__main__':
	app.run(host='Localhost',debug=True,threaded=False)