# Requirements
## User Stories
- As a user, when I request a refund through the client’s support assistant, I want to be guided through the refund process and informed about the eligibility criteria and expected processing time, after I provide the order number, a description of the products to be refund and quantity to refund.

- As a user, when I call the client's support assistant and ask to reschedule my order, I want my order to be reschedule, after I provide the order number and ask for the customer pre-availability with restriction, like 24h. 

- As a user,when I request information outside the assistant’s predefined scope, I want the assistant to create a ticket by summarizing our conversation and sending the information to the client’s support team to resolve my issue.

- As a user, when I inquire about return policies, I want the assistant to clearly explain the return process, deadlines, and any necessary conditions.

- As a user, when I call the voice assistant, I want to be greeted and informed about what kind of help the assistant can provide so that I understand its purpose and role.

- As a user, when I ask a question that requires additional details (e.g., an order number or product specifics), I want the assistant to ask for this information, so the response can be accurate and complete.

- As a user, when I speak with the voice assistant, I want the conversation to feel natural, fluid, and free from robotic pauses, so the experience feels similar to speaking with a human.

- As a user, when I inquire about my order but can’t remember my order number, I want the assistant to ask for an alternative, such as my email address or other account details, to retrieve my order information.

- As a user, when I call the voice assistant and provide my order number, I want the assistant to categorize my request and proceed with the correct process.

## User Case Model

|||
| --- | --- |
| *Name* | Apoio ao Cliente com Assistente de Voz |
| *Actor* | Customer | 
| *Description* | This project aims to develop an AI-powered concierge solution to serve as the first line of support for the Continente Online Voice Channel. The AI assistant will handle customer inquiries and requests by answering calls, actively listening, and categorizing interactions. It will provide automated responses using the Continente Online public knowledge base and escalate complex issues by generating structured summaries and support tickets for manual processing.<br> Designed to deliver a seamless and human-like conversational experience, the solution will ensure natural interactions, effective pause management, and avoidance of robotic speech.|
| *Preconditions* | - The customer is a client of Continente Online. |
| *Postconditions* | - The customer has is problem fix. <br> - The customer will have is problem send to a specific team to solve is problem. |
| *Normal flow* | 1. The customer calls the Continente Online client's support. <br> 2.The customer explain is problem to the assintant. <br> 3.The AI assistant ask for more information about the problem, like the order number. <br> 4.The customer gives the extra information <br> 5.The AI assistant will fix the problem and give the customer the next steps that he needs to take. <br> 6. The AI assistant will create an output JSON file with the client's information, typification, a summary of the conversation, and other information like products. |
| *Alternative flows and exceptions* | In step 5, if the AI assistant can't fix the problem he will create a ticket and send to the client's support with the information gathered and a summarization of the conversion.|