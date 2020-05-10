class SamResourceType(Enum):
    """
    Enum of supported SAM types
    """

    Api = "AWS::Serverless::Api"
    Function = "AWS::Serverless::Function"
    SimpleTable = "AWS::Serverless::SimpleTable"
    Application = "AWS::Serverless::Application"
    LambdaLayerVersion = "AWS::Serverless::LayerVersion"
    HttpApi = "AWS::Serverless::HttpApi"

    @classmethod
    def has_value(cls, value):
        """
        Checks if the given value belongs to the Enum
        :param string value: Value to be checked
        :return: True, if input is in the Enum
        """
        return any(value == item.value for item in cls)