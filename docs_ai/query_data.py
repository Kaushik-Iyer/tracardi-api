import os
from pprint import pprint

import weaviate

from docs_ai.utils import get_chat_gpt3_response, get_chat_gpt3_5_response

client = weaviate.Client(
    url="http://192.168.1.190:8080/",  # Replace with your endpoint
    additional_headers={
        "X-OpenAI-Api-Key": os.environ.get('API_KEY', "None")  # Replace with your inference API key
    }
)

"What are the key definitions in tracardi"
"What is session"
"How can I bind event to button click"
"What is profile"
"Where tracardi stores profile visits."
"What is dot notation."
"How do I filter the data."
"How do I import mongodb data to tracardi."
"I got error Invalid API"
"How I I send email in Tracardi"  # *
"Can I send marketing campaigns from tracardi"
"Can I send SMSes with tracardi"  #
"How Do I install extensions"  #

question = """
How to upgrade tracardi?
"""
nearText = {"concepts": [question]}

result = (
    client.query
        .get("Tracardi", ["question", "answer"])
        .with_additional(["distance"])
        .with_near_text(nearText)
        .with_limit(10)
        .do()
)

answers = []
skip_answers = {}
for item in result['data']['Get']['Tracardi']:
    distance = item['_additional']['distance']
    if distance > 0.2:
        continue
    if item['answer'] in skip_answers:
        continue
    skip_answers[item['answer']] = 1
    answers.append((item['answer'], distance))

context = ""
n = 0
for answer, distance in answers:
    n += 1
    context += f"\n\n-- Document part {n} (Distance: {distance}) --\n{answer}"

prompt = f"""I have this documentation on Tracardi system. It is set up of document parts that try to answer the question: "{question}".  
Each part has distance metrics which is a distance from question to answer in terms of cosine similarity. 
The smaller distance the better source of information. 
Find the most accurate document parts combine them and answer in detail the question: "{question}". 
Do not use the parts that seems irrelevant to the asked question. If you think that the answer 
can not be found in provided information or the answer may be inaccurate - respond with \"I can't answer this question\". 
Respond only with answer.

Use this documentation: {context}
"""

print(f"RPMPT: {prompt}")

print("-----")
chatgpt3_context = get_chat_gpt3_response(prompt[:4090])
print(chatgpt3_context)
print("---CHAT4---")
response = get_chat_gpt3_5_response(system="You are an expert on Tracardi system with the access to MD files with documentation.",
                               user=f"Context: {chatgpt3_context}\n{prompt[:4090]}",
                               assistant=f"""
                               These are the fundamentals of how tracardi works. 
                               Tracardi works by collecting data in the form of events, which correspond to customer actions. These events are categorized into event types, such as product purchases, and are stored in profiles. Profiles are maintained throughout the customer interaction and aggregate customer journey data using a graphical editor.

To engage customers, Tracardi utilizes workflows, which are a series of actions executed in response to events. Workflows are represented as a graph of nodes in Tracardi's graphical interface and define how to engage customers at different stages of their customer journey.

Event routing rules in Tracardi determine which workflow to execute based on the arrival of defined event types. This automation ensures the appropriate workflow is triggered based on specific events and associated workflows.

Tracardi integrates with various data sources, including incoming traffic from websites and internal systems. It can also send outgoing data to external systems or destinations, enabling seamless data integration.

Core definitions:

    Data in Tracardi is represented as events, which are recognized actions or occurrences.
    Each event is assigned to a profile that remains consistent throughout customer interactions.
    Tracardi utilizes a graphical editor to aggregate customer journey data into profiles.
    Customer consents can be utilized within Tracardi.
    Tracardi enhances customer engagement through micro frontend applications, such as website pop-ups for collecting customer answers.
    Tracardi does not support marketing campaigns.
    The data processing library in Tracardi handles workflows and enables plugin development.
    Tracardi provides a graphical interface for creating, editing, and managing workflows.
    Workflows consist of nodes representing actions.
    Parameters can be configured to customize the behavior of each action node in a workflow.
    Workflows are executed in response to events.
    Tracardi receives incoming traffic, which includes data from websites and internal systems.
    Outgoing traffic from Tracardi is sent to external systems or destinations.
    Bridges collect data from specific sources (e.g., queue, email, social media).
    Event sources in Tracardi are identified by unique identifiers generated by the system.
    Event sources require bridges for data transfer.
    Event sources can be set as ephemeral, where data is processed but not permanently stored.
    Resources in Tracardi are sets of authentication credentials (e.g., passwords, tokens) for accessing external systems and databases.
    Sessions in Tracardi are associated with visits to websites or applications.
    Sessions contain context information about the events' context.
    Events in Tracardi represent actions occurring at specific times.
    Events track visitor behavior, such as clicks, logins, and page views.
    Events can capture additional data related to the event.
    Tracardi stores events and passes them to workflows for processing.
    Routing rules determine which workflows to execute based on event arrival.
    Routing rules automate workflow execution based on specific events.
    Routing rules consist of event type, event source, and the associated workflow.
    Workflows in Tracardi are a series of actions executed in response to events.
    Workflows are represented as graphs of nodes.
    Actions within workflows are assigned to individual nodes.
    Workflows run only if the event type is routed to them through routing rules.
    Actions are individual tasks performed within workflows, also known as workflow plugins.
    Actions receive data through input ports and send data through output ports.
    Actions can be extended using custom code written by programmers.
    Profiles in Tracardi are detailed records or representations of individuals or entities.
    Profiles contain information about characteristics, interests, and activities.
    Profiles are updated based on incoming events and data from external systems.
    Segment is a group of customer profiles based on shared characteristics or behavior.
    Destination is an external system where profile data is sent from Tracardi.
    Customer consent is a permission obtained from individuals to collect, use, or share their personal data.
    Data compliance is adherence to laws, regulations, and guidelines for handling data.
    Identification point is a feature allowing the system to identify customers during their journey.
    User/Customer is anonymous until the identification point is reached.
    Identification point enables merging of previous interactions/events with the identified profile.
    Tracardi can be integrated with mobile apps or external systems.
                               """)

print(response['content'])
# print(json.dumps(result, indent=4))
