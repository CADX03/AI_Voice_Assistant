
import random
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class CheckOrderExists(Action):
    def name(self) -> str:
        return "action_check_order_exists"

    def run(
        self,
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[str, Any]
    ) -> List[Dict[Text, Any]]:
        order_exists = True
        return [SlotSet("order_exists", order_exists)]
