from haystack import Pipeline
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.utils import Secret
from haystack import component
from bson import ObjectId
from pymongo import MongoClient
from typing import List, Optional
from dotenv import load_dotenv
import os

load_dotenv()


@component
class MongoDataFetcher:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URL"))
        self.collection = self.client["LastNotification"]["users"]

    @component.output_types(messages=list[ChatMessage])
    def run(self, id: str = None, res_to_fix: list[ChatMessage] = None):
        if id is not None and res_to_fix == None:
            print("idelepbe")
            document = self.collection.find_one({"_id": ObjectId(id)})
            if not document:
                raise LookupError

            name = document["name"]
            messages = [
                ChatMessage.from_system(
                    "You are a helpful and motiviating assistant that creates motivational messages. Try to keep them short. Suggest some low intesity activity for them to do "
                ),
                ChatMessage.from_user(f"Create a notification for this person {name}"),
            ]
            return {"messages": messages}

        if res_to_fix != None:
            print(id)
            messages = [
                ChatMessage.from_system(
                    "You are a message shortener tool, shorten messages that are being sent to you to less then 120 chars "
                ),
                ChatMessage.from_user(
                    f"Fix this notification this is too long {res_to_fix[0].text} max 120 chars including whitespace"
                ),
            ]
            return {"messages": messages}


@component
class OutputValidator:
    def __init__(self):

        pass

    @component.output_types(
        valid_reply=List[ChatMessage],
        invalid_replies=List[ChatMessage],
        error_message=Optional[str],
    )
    def run(self, reply: List[ChatMessage]):
        try:
            motivation = reply[0].text

            if validate(motivation):
                print("belep")
                return {"valid_replies": reply}
            else:
                print("belep23")
                return {"invalid_replies": reply}
        except ValueError as e:

            return {"invalid_replies": reply}


def validate(msg: str) -> bool:

    letter_count = len(msg)
    whitespaceCount = 0
    for i in range(len(msg) - 1):
        if msg[i].isspace():
            whitespaceCount += 1

    if whitespaceCount > 20:
        print("False")
        return False
    elif whitespaceCount < 20 and letter_count < 130:
        print("True")
        return True
    else:
        print("False")
        return False


# Initialize the generator
generator = OpenAIChatGenerator(
    model="gpt-4o-mini",
    api_key=Secret.from_token(os.getenv("OPENAI_API_KEY")),
)

# Create the pipeline
pipeline = Pipeline(max_runs_per_component=5)
pipeline.add_component("validator", OutputValidator())
# Add both components
pipeline.add_component("fetcher", MongoDataFetcher())
pipeline.add_component("generator", generator)

# Connect them
pipeline.connect("fetcher", "generator")
pipeline.connect("generator.replies", "validator")
pipeline.connect("validator.invalid_replies", "fetcher.res_to_fix")
