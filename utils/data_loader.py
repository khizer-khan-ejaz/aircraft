from allclass import *
import ast
PREDEFINED_2_MARK_QUESTIONS = [
    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}. TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Launceston",
        "arr_name_text": "East sale",
        "track_name": "W-218",
        "etp_dest1_name_text": "East sale",
        "etp_dest2_name_text": "Latrobe Valley",
        "reference": "L1",
    },
    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}. TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "reference": "L2",
        "dep_name_text": "Griffith",
        "arr_name_text": "Mildura",
        "track_name": "W-415",
        "etp_dest1_name_text": "Mildura",
        "etp_dest2_name_text": "Swan Hill",
    },
 
    {
    "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}. TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
    "dep_name_text": "Inverell",
    "arr_name_text": "Walgett",
    "track_name": "W623",
    "tas": "200 kt",
    "wind_dir_display": "290",
    "wind_speed": "55",
    "etp_dest1_name_text": "Walgett",
    "etp_dest2_name_text": "Narrabri",
    "reference": "L3"
    },

    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Emerald",
        "arr_name_text": "Charleville",
        "track_name": "W806",
        "etp_dest1_name_text": "Charleville",
        "etp_dest2_name_text": "Roma",
        "reference": "L4",
    },
        {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Dubbo ",
        "arr_name_text": "Bourke ",
        "track_name": "W540",
        "etp_dest1_name_text": "Bourke ",
        "etp_dest2_name_text": "Walgett ",
        "reference": "L5",
    },
       {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Tindal",
        "arr_name_text": "Tennant Creek",
        "track_name": "J30",
        "etp_dest1_name_text": "Tennant Creek",
        "etp_dest2_name_text": "Hooker Creek",
        "reference": "L6",
    },
    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Whyalla ",
        "arr_name_text": "Coober Pedy",
        "track_name": "W274",
        "etp_dest1_name_text": "Coober Pedy",
        "etp_dest2_name_text": "Woomera",
        "reference": "L7",
    },
    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Newman ",
        "arr_name_text": "Port Hedland",
        "track_name": "W125",
        "etp_dest1_name_text": "Port Hedland",
        "etp_dest2_name_text": "Paraburdoo",
        "reference": "L8",
    },
]
# Initialize generator
generator = AirportQuestionGenerator(sample_airports)
def find(name,airports):
    """Find airport in airports_list by name (case insensitive partial match)"""
    name_lower = name.lower()
    for airport in airports:
        if name_lower in airport.name.lower():
            return airport  # Return the Airport object directly
    return None
def load_airport_data(filepath="data.txt"):
    with open(filepath, "r") as f:
        content = f.read()
    return ast.literal_eval(content)

AIRPORT_DATA = load_airport_data()