// Load the AWS SDK for JS
var AWS = require("aws-sdk");
AWS.config.update({region: 'us-east-1'});

// Load the UUID library
const uuidv4 = require('uuid/v4');

// Create the DynamoDB Document Client
var dynamodb = new AWS.DynamoDB.DocumentClient();
var tableName = process.env.DYNAMODB_TABLE

module.exports.create = async function(body) {
    const customer_id = body['customer_id']
    const survey_id = uuidv4()
    const survey_data = body['survey_data']
    const putParams = {
        TableName: tableName,
        Item: {
            'pk': 'CUSTOMER#' + customer_id,
            'sk': 'SURVEY#' + survey_id,
            'survey_data': survey_data
        }
    }
    try {
        await dynamodb.put(putParams).promise()
        return {
            "survey_id": survey_id
        }
    } catch (error) {
        console.log(error)
        throw new Error(error)
    }
}


module.exports.get = async function(survey_id) {
    const queryParams = {
        TableName: tableName,
        IndexName: 'sk-pk-index',
        KeyConditionExpression: 'sk = :sk',
        ExpressionAttributeValues: {
            ':sk': 'SURVEY#' + survey_id
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


module.exports.getAll = async function(customer_id) {
    const queryParams = {
        TableName: tableName,
        KeyConditionExpression: 'pk = :pk AND begins_with ( sk , :sk )',
        ExpressionAttributeValues: {
            ':pk': 'CUSTOMER#' + customer_id,
            ':sk': 'SURVEY#'
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
