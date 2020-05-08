const serverless = require('serverless-http')
const express = require('express')
const app = express()
var customers = require('./entities/customers');
var surveys = require('./entities/surveys');
var responses = require('./entities/responses');

app.post('/customer', async function (req, res) {
  const body = JSON.parse(req.body)
  const response = await customers.create(body)
  res.send(response)
})

app.get('/customer/:customer_id', async function (req, res) {
  const customer_id = req.params.customer_id
  const response = await customers.get(customer_id)
  res.send(response)
})

app.get('/customer/:customer_id/surveys', async function (req, res) {
  const customer_id = req.params.customer_id
  const response = await surveys.getAll(customer_id)
  res.send(response)
})

app.get('/survey/:survey_id', async function (req, res) {
  const survey_id = req.params.survey_id
  const response = await surveys.get(survey_id)
  res.send(response)
})

app.post('/survey', async function (req, res) {
  const body = JSON.parse(req.body)
  const response = await surveys.create(body)
  res.send(response)
})

app.get('/survey/:survey_id/responses', async function (req, res) {
  const survey_id = req.params.survey_id
  const response = await responses.getAll(survey_id)
  res.send(response)
})

app.get('/response/:response_id', async function (req, res) {
  const response_id = req.params.response_id
  const response = await responses.get(response_id)
  res.send(response)
})

app.post('/response', async function (req, res) {
  const body = JSON.parse(req.body)
  const response = await responses.create(body)
  res.send(response)
})


module.exports.handler = serverless(app)
