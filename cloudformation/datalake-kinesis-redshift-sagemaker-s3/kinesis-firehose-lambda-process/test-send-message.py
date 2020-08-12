const AWS = require("aws-sdk");

AWS.config.apiVersions = {
    kinesis: '2013-12-02'
};
  
const firehose = new AWS.Firehose({
    region: "us-east-1"
});


const main = async() => {

    const message = {"message":"abc" };

    var params = {
        Record: {
            Data: JSON.stringify(message)
        },
        DeliveryStreamName: 'test-DeliveryStream-1PMIBGYAJIE1'
      };

     let data = await firehose.putRecord(params).promise();
     console.log("Done: "+JSON.stringify(data));

}

main();