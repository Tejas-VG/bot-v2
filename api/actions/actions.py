# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import Restarted, EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher

from main import Dose_Availability_District, Dose_Availability_Pincode, Dose_Availability_Lon_Lat, send_email

class ActionPincodeSubmit(Action):

    def name(self) -> Text:
        return "action_pincode_submit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global message
        message=Dose_Availability_Pincode(tracker.get_slot('pincode'),tracker.get_slot('date'))
        dispatcher.utter_message(text=message)
        buttons = [
            {'payload': "/affirm", 'title': "Yes"},
            {'payload': "/deny", 'title': "No"},
        ]
        dispatcher.utter_message(text="Would you like to get the details on your email id?",buttons=buttons)

        return [SlotSet("pincode", None), SlotSet("date", None)]

class ActionDistrictSubmit(Action):

    def name(self) -> Text:
        return "action_district_submit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global message
        message=Dose_Availability_District(tracker.get_slot('district_id'),tracker.get_slot('date'))
        dispatcher.utter_message(text=message)
        buttons = [
            {'payload': "/affirm", 'title': "Yes"},
            {'payload': "/deny", 'title': "No"},
        ]
        dispatcher.utter_message(text="Would you like to get the details on your email id?",buttons=buttons)

        return [SlotSet("district_id", None), SlotSet("date", None)]

class ActionLocationSubmit(Action):

    def name(self) -> Text:
        return "action_location_submit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global message
        message=Dose_Availability_Lon_Lat(tracker.get_slot('lattitude'),tracker.get_slot('longitude'))
        dispatcher.utter_message(text=message)
        buttons=[
            {'payload':"/affirm",'title':"Yes"},
            {'payload':"/deny",'title':"No"},
        ]
        dispatcher.utter_message(text="Would you like to get the details on your email id?",buttons=buttons)
        return [SlotSet("lattitude", None), SlotSet("longitude", None)]

class ActionSendEmail(Action):

    def name(self) -> Text:
        return "action_send_mail"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        status = send_email(tracker.get_slot("email"), message)
        if status == "success":
            dispatcher.utter_message(text="We have successfully sent the mail to your Email ID: {}".format(tracker.get_slot("email")))
        else:
            dispatcher.utter_message(text=f"⚠️ {status}")

        return []

class ActionRestart(Action):

    def name(self) -> Text:
      return "action_restart"

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

      return [Restarted()]


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        import os
        import requests

        user_message = tracker.latest_message.get('text')
        
        # Look for Groq API Key in file or env variable
        api_key = os.environ.get("GROQ_API_KEY")
        key_file_path = os.path.join(os.path.dirname(__file__), "..", "groq_key.txt")
        
        if not api_key and os.path.exists(key_file_path):
            with open(key_file_path, "r", encoding="utf-8") as f:
                api_key = f.read().strip()
                
        if not api_key:
            dispatcher.utter_message(
                text="Please set your Groq API key in `api/groq_key.txt` or as a `GROQ_API_KEY` environment variable to enable AI answers."
            )
            return []
            
        # Call Groq API
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are the AI assistant for MAYDEN SMARTHEALTH PVT LTD.\n"
                            "Your primary function is to help users check vaccination slot availability near them "
                            "and answer questions related to COVID-19, vaccines, vaccination centers, eligibility, "
                            "and general health queries.\n"
                            "Always maintain this persona:\n"
                            "1. Be helpful, professional, and friendly.\n"
                            "2. If the user asks something completely unrelated to vaccines, COVID-19, health, "
                            "or vaccination slots, politely decline to answer, and guide them back to checking "
                            "for vaccine slot availability (by Pincode, District ID, or Latitude/Longitude)."
                        )
                    },
                    {"role": "user", "content": user_message}
                ]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response_json = response.json()
            
            if response.status_code == 200:
                choices = response_json.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    dispatcher.utter_message(text=content)
                    return []
            
            # If API response was not successful
            error_msg = response_json.get("error", {}).get("message", "Unknown error")
            dispatcher.utter_message(text=f"Groq API returned an error: {error_msg}")
        except Exception as e:
            dispatcher.utter_message(text=f"Error calling Groq API: {str(e)}")
            
        return []


# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
