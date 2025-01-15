instruction_list = [
"Get a name of ticker as input",
"Call the tool perform_calculations_for_tickers to get all of the calculations and data",
"the tool will send you the features so provide them to the user",
"user migh ask multiple questiosn or want to create a portfolio try to answer the user with newly generated data",
"the datetime is passed use it for selecting the data range",
"if no datetime provided, get the last two years data",
"all of the data should be daily so if the user wanted other periods, is not available for now",

]

guideline_list = [

]


def get_prompts():
    return instruction_list, guideline_list