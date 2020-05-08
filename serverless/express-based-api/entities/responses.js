// Load the AWS SDK for JS
var AWS = require("aws-sdk");
AWS.config.update({region: 'us-east-1'});

// Load the UUID library
const uuidv4 = require('uuid/v4');

// Create the DynamoDB Document Client
var dynamodb = new AWS.DynamoDB.DocumentClient();
var tableName = process.env.DYNAMODB_TABLE

module.exports.create = async function(body) {
    const survey_id = body['survey_id']
    const response_id = uuidv4()
    const response_data = body['response_data']
    const putParams = {
        TableName: tableName,
        Item: {
            'pk': 'RESPONSE#' + response_id,
            'sk': 'SURVEY#' + survey_id,
            'response_data': response_data
        }
    }
    try {
        await dynamodb.put(putParams).promise()
        return {
            "response_id": response_id
        }
    } catch (error) {
        console.log(error)
        throw new Error(error)
    }
}

module.exports.get = async function(response_id) {
    const queryParams = {
        TableName: tableName,
        KeyConditionExpression: 'pk = :pk',
        ExpressionAttributeValues: {
            ':pk': 'RESPONSE#' + response_id
        }
    }
    try {
        const queryResult = await dynamodb.query(queryParams).promise()
        console.log(queryResult)
        return queryResult['Items'][0]
    } catch (error) {
        console.log(error)
        throw new Error(error)
    }
}


module.exports.getAll = async function(survey_id) {
    const queryParams = {
        TableName: tableName,
        IndexName: 'sk-pk-index',
        KeyConditionExpression: 'sk = :sk AND begins_with ( pk , :pk )',
        ExpressionAttributeValues: {
            ':pk': 'RESPONSE#',
            ':sk': 'SURVEY#' + survey_id
        }
    }
    try {
        const queryResult = await dynamodb.query(queryParams).promise()
        console.log(queryResult)
        return queryResult['Items']
    } catch (error) {
        console.log(error)
        throw new Error(error)
    }
}
