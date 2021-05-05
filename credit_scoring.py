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
	score, age, gender, bank_account, repayment, vol_trans, airtime = compute_score(elt, *model)
	return jsonify({'Score': score,
		   			'age': age,
		   			'gender': gender,
		   			'bank_account': bank_account,
					'repayment':repayment,
		            'vol_trans': vol_trans,
		            'airtime': airtime})


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


	age = weights['Age']*Options['Age'][row['Age']]
	gender = weights['Gender']*Options['Gender'][row['Gender']]
	bank_account = weights['Bank_account']*Options['Bank_account'][row['Bank_account']]
	repayment = weights['Due date - repayment date']*float(row['Due date - repayment date'])
	vol_trans = weights['Volume of transactions']*float(row['Volume of transactions'])
	airtime = weights['Airtime']*float(row['Airtime'])


	# Normalisation constant
	norm_const = age + gender + bank_account + repayment + vol_trans + airtime

	age = age/norm_const
	gender = gender/norm_const
	bank_account = bank_account/norm_const
	repayment = repayment/norm_const
	vol_trans = vol_trans/norm_const
	airtime = airtime/norm_const

	return normalize_score(score, Min, Max), age, gender, bank_account, repayment, vol_trans, airtime


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=5000)