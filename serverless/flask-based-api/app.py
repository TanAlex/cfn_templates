from flask import Flask
from flask import request
from entities import customers
from entities import surveys
from entities import responses

app = Flask(__name__)


@app.route('/customer', methods=['POST'])
def create_customer():
    payload = request.get_json()
    return customers.create(payload)
    

@app.route("/customer/<customer_id>", methods=['GET'])
def get_customer(customer_id):
    return customers.get(customer_id)


@app.route("/customer/<customer_id>/surveys", methods=['GET'])
def get_customer_surveys(customer_id):
    return surveys.get_all(customer_id)


@app.route('/survey', methods=['POST'])
def create_survey():
    payload = request.get_json()
    return surveys.create(payload)


@app.route("/survey/<survey_id>", methods=['GET'])
def get_survey(survey_id):
    return surveys.get(survey_id)


@app.route("/survey/<survey_id>/responses", methods=['GET'])
def get_survey_responses(survey_id):
    return responses.get_all(survey_id)


@app.route('/response', methods=['POST'])
def create_response():
    payload = request.get_json()
    return responses.create(payload)


@app.route("/response/<response_id>", methods=['GET'])
def get_response(response_id):
    return responses.get(response_id)
