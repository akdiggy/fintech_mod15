# Required Libraries
from datetime import datetime
from dateutil.relativedelta import relativedelta
from botocore.vendored import requests

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response

def validate_data(age, investmentAmount, riskLevel, intent_request):
   
    # Make sure the age is greater than zero, but less than 66
    if age is not None:
        
        # Convert the number variables before doing the conditional logic once it is verified it is not null 
        age = parse_int(age)
        
        if (age < parse_int(0)) or (age > parse_int(65)):
        
           return build_validation_result(
               False,
               "age",
               "You entered an age that does not fall within the age range for this utility. Please enter an age between 1 and 65."
            )
        
    # The investment amount needs to be greater than or equal to $5000
    if investmentAmount is not None:
        
        # Convert the number variables before doing the conditional logic once it is verified it is not null 
        investmentAmount = parse_int(investmentAmount)
    
        if investmentAmount < int(5000):
        
           return build_validation_result(
               False,
               "investmentAmount",
               "You must enter an investment amount greater than or equal to $5000."
            )
        
    # You must enter a value of either None/Low/Medium/High    
    
    if riskLevel != None:
        
        if (riskLevel != "none") and (riskLevel != "low") and (riskLevel != "medium") and (riskLevel != "high"):
            
           return build_validation_result(
               False,
               "riskLevel",
               "You did not enter a valid risk level for this utility. Please enter either none or low or medium or high."
            )
           
    # A True results is returned if age, investment amount and risk level are valid
    return build_validation_result(True, None, None)

### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """
    
    firstname = get_slots(intent_request)["firstname"]
    age = get_slots(intent_request)["age"]
    investmentAmount = get_slots(intent_request)["investmentAmount"]
    riskLevel = get_slots(intent_request)["riskLevel"]
    
    # Gets the invocation source, for Lex dialogs "DialogCodeHook" is expected.
    source = intent_request["invocationSource"]
    
    if source == "DialogCodeHook":
         
        # This code performs basic validation on the supplied input slots.
         
        # Get all the slots
        slots = get_slots(intent_request)
         
        # Validates user's input using the validate_data function
        validation_result = validate_data(age, investmentAmount, riskLevel, intent_request)
        
        # If the data provided by the user is not valid,
        # the elicitSlot dialog action is used to re-prompt for the first violation detected.
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None  # Cleans invalid slot

            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        # Fetch current session attributes
        output_session_attributes = intent_request["sessionAttributes"]
        
        # Once all slots are valid, a delegate dialog is returned to Lex to choose the next course of action.
        return delegate(output_session_attributes, get_slots(intent_request))
        
    invest_advice = get_advice(riskLevel)
    
    # Return a message with the customer's investment advice.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """Based on your risk level, it is recommended that your portfolio should be {}
            """.format(
                invest_advice
            )
        }
        
    )

### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")
    
def get_advice(risklevel):
    
    # Give an investment recommendation based on the customer's risk level of None/Low/Medium/High
    
    if risklevel == 'none':
        advice = '100% bonds (AGG), 0% equities (SPY)'
    elif risklevel == 'low':
        advice = '60% bonds (ACG), 40% equities (SPY)'
    elif risklevel == 'medium':
        advice = '40% bonds (ACG), 60% equities (SPY)'
    else:
        advice = '20% bonds (ACG), 80% equities (SPY)'
        
    return advice 
    


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)
