# Hauptprompt von GeoAgent. Orientiert an MotleyCrew: https://motleycrew.readthedocs.io/en/latest/_autosummary/motleycrew.agents.langchain.tool_calling_react_prompts.html#module-motleycrew.agents.langchain.tool_calling_react_prompts

import json

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate


def getPrompt(prompt: str):
    """Erstellt ein ChatPromptTemplate aus einem eigenem Text oder einem Standardtext 
    
    Args: 
        main_prompt: Der zu verwendene Text. Muss die Platzhalter gdfs_num, gdfs_infos enthalten.
    """
    
    main_prompt = prompt if prompt else  """You are a geospatial analyst. You should solve spatial analysis tasks based on GeoDataFrames (in EPSG:25832) or DataFrames (without geometry column) and/or OpenStreetMap. Use a tool only if you can't answer a question directly. If necessary, retrieve additonal OSM data and/or perform geocoding to support the task. Make sure to always visualize relevant GeoDataFrames. If necessary transform coordinates to EPSG:25832. You can directly use the following {gdfs_num} (Geo-)DataFrames which are available in the python environment: 
    {gdfs_infos}."""
    
    react_prompt = """
    Answer the following questions as best you can.
    Think carefully, one step at a time, and outline the next step towards answering the question. 
    To use tools, you must first describe what you think the next step should be, and then if necessary call the tool or tools to get more information.
    In this case, your reply must begin with \"Thought:\" and describe what the next step should be, given the information so far.
    The reply must contain the tool call or calls that you described in the thought.
    You may include multiple tool calls in a single reply, if necessary.
    
    If the information so far is not sufficient to answer the question precisely and completely (rather than sloppily and approximately), don't hesitate to use tools again, until sufficient information is gathered.
    Don't stop this until you are certain that you have enough information to answer the question.
    
    If you know the answer or you have sufficient information to answer the question, don't use a tool and provide the answer immediately without any further thought process.

    Begin!
    """
    
    prompt = main_prompt + react_prompt
    
    example_messages = [
        SystemMessage("Here is an example of how to use tools:"),
        AIMessage(
            content="Thought: <your thought here>",
            additional_kwargs={
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "call_aSuMulBd6JVrHCMjyKSi93na",
                        "function": {
                            "arguments": json.dumps(dict(arg_one="value_one", arg_two="value_two")),
                            "name": "tool_name",
                        },
                        "type": "function",
                    }
                ]
            },
        ),
        ToolMessage(
            content="<tool response>",
            tool_call_id="call_aSuMulBd6JVrHCMjyKSi93na",
        ),
        AIMessage(content="OK, I will always write a thought before calling a tool."),
    ]

    reminder_message = SystemMessage(
        """Is a tool needed?
        If yes, your reply MUST begin with "Thought:" and describe what the next step should be.
        The reply must contain the tool call or calls that you described in the thought.
        TOOL CALLS WITHOUT A THOUGHT WILL NOT BE ACCEPTED!
        
        Else, if you know the answer or you have sufficient information to answer the question, provide the answer immediately without any further thought process.
        
        Write your reply, starting with either "Thought:" or give the answer:
        """
    )
    
    prompt_template = ChatPromptTemplate.from_messages(
        [   
            ("system", prompt), 
            MessagesPlaceholder(variable_name="example_messages", optional=True), 
            MessagesPlaceholder(variable_name="chat_history"), 
            HumanMessagePromptTemplate.from_template("{input}"), 
            MessagesPlaceholder(variable_name="agent_scratchpad") 
        ]
    )
    
    prompt_template = prompt_template.partial(example_messages=example_messages)
    prompt_template.append(reminder_message)
    return prompt_template

    
