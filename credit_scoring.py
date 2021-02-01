from flask import Flask, request, jsonify
import pickle

# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import firestore

model_file = 'credit_object.pkl'
token = 'KOLA2019#'

criteria = ['Gender', 'Age', 'bank_account']

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
	row = request.get_json(force=True)
	del row['Sector']
	Options, weights, Min, Max = deserialize_model(model_file)
	score = compute_score(row, Options, weights)
	score = normalize_score(score, Min, Max)
	return jsonify({'Score': score}) if score <= 1.0 else jsonify({'Score' : 1.0})


def entries_verification():
	pass


def deserialize_model(model_file):
	with open(model_file, mode='rb') as file:
		model = pickle.load(file)
	return tuple(model.values())


def normalize_score(score, Min, Max):
	return (score - Min)/(Max - Min)


def compute_score(row, Options, weights):
	score = 0
	for criterion in row:
	    if criterion in criteria: # For categorical criterion
	        score += weights[criterion]*Options[criterion][row[criterion]]
	    else: # For numerical criterion
	        score += weights[criterion]*float(row[criterion])
	return score


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=5000)