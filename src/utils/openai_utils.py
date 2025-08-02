import openai

from src.settings import settings

# LLM model configuration
LLM_MODEL = settings.llm_model

openai.api_key = settings.openai_api_key


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

    response = openai.chat.completions.create(
        model=LLM_MODEL, messages=messages, temperature=settings.temperature
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

    kwargs = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": settings.temperature,
    }

    if response_format is not None:
        kwargs["response_format"] = response_format

    response = openai.chat.completions.create(**kwargs)

    return response.choices[0].message.content
