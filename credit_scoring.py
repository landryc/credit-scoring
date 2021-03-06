from flask import Flask, request, jsonify
import pickle

model_file = 'credit_object.pkl'
token = 'KOLA2019#'

criteria = ['Gender', 'Age', 'Bank_account']

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index_page():
	#rceturn render_template('Bonjour')
	return jsonify({'message': 'Je teste la construction d\'api'})

@app.route('/predict', methods=['POST', 'GET'])
def predict_logic():
	# Authentifcation process
	if 'Authorization' not in request.headers.keys():
		return jsonify({'Score':'Not authorization'})
	if request.headers['Authorization'] != token:
		return jsonify({'Score': 'Authentification failed'})

	# Compute the score
	elt = request.get_json(force=True)
	elt = prepare_data(elt)
	model  = deserialize_model(model_file)
	score, repayment, vol_trans, bank_account, airtime, age, gender = compute_score(elt, *model)
	return jsonify({'Score': score,
		 			'repayment': repayment,
		   			'vol_trans': vol_trans,
		   			'bank_account': bank_account,
		            'airtime': airtime,
		            'age': age,
		            'gender': gender,})


def prepare_data(row):
	# Encoding Age variable
	if row['Age'] < 25:
		row['Age'] = '18-24'
	elif row['Age'] in range(25,35):
		row['Age'] = '25-34'
	elif row['Age'] in range(35,45):
		row['Age'] = '35-44'
	elif row['Age'] in range(45,55):
		row['Age'] = '45-54'
	elif row['Age'] in range(55,65):
		row['Age'] = '55-64'
	else:
		row['Age'] = '65+'

	return row


def deserialize_model(model_file):
	with open(model_file, mode='rb') as file:
		model = pickle.load(file)
	return tuple(model.values())


def normalize(elt, norm_params):
    for criterion in norm_params.keys():
        elt[criterion] = elt[criterion] / norm_params[criterion]
    return elt


def normalize_score(score, Min, Max):
	# First normalization : Put the score between [0, 1]
	score = (score - Min)/(Max - Min)
	score = score if score <= 1.0 else 1.0
	
	# Second normalization : Put the score between [MIN, MAX]
	MIN = 300
	MAX = 860
	return score * MAX + (1 - score) * MIN 	


def compute_score(elt, Options, weights, Min, Max, norm_params):
	score = 0
	row = normalize(elt, norm_params)
	for criterion in row:
	    if criterion in criteria: # For categorical criterion
	        score += weights[criterion]*Options[criterion][row[criterion]]
	    else: # For numerical criterion
	        score += weights[criterion]*float(row[criterion])


	age = Options['Age'][row['Age']]
	gender = Options['Gender'][row['Gender']]
	bank_account = Options['Bank_account'][row['Bank_account']]
	repayment = float(row['Due date - repayment date'])
	vol_trans = float(row['Volume of transactions'])
	airtime = float(row['Airtime'])


	# Compute the maximum values for normalization
	max_age = Options['Age'].values.max()
	max_gender = Options['Gender'].values.max()
	max_bank_account = Options['Bank_account'].values.max()

	# Normalisation constant

	age = age/max_age
	gender = gender/max_gender
	bank_account = bank_account/max_bank_account
	repayment = 1.0 if repayment > 1.0 else repayment
	vol_trans = 1.0 if vol_trans > 1.0 else vol_trans
	airtime = 1.0 if airtime > 1.0 else airtime

	return normalize_score(score, Min, Max), repayment, vol_trans, bank_account, airtime, age, gender


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=5000)
