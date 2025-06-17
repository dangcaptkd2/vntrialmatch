import openai

from config.config import LLM_MODEL, OPENAI_API_KEY, TEMPERATURE

openai.api_key = OPENAI_API_KEY


def get_llm_response(prompt, system_message=None):
    """
    Get response from LLM model.

    Args:
        prompt (str): The user prompt
        system_message (str, optional): System message for context

    Returns:
        str: LLM response
    """
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})

    response = openai.ChatCompletion.create(
        model=LLM_MODEL, messages=messages, temperature=TEMPERATURE
    )

    return response.choices[0].message.content


def get_structured_llm_response(prompt, system_message=None, response_format=None):
    """
    Get structured response from LLM model.

    Args:
        prompt (str): The user prompt
        system_message (str, optional): System message for context
        response_format (dict, optional): Expected response format

    Returns:
        dict: Structured LLM response
    """
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})

    response = openai.ChatCompletion.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        response_format=response_format,
    )

    return response.choices[0].message.content
