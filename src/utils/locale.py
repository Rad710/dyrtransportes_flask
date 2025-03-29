from flask import request


def get_locale() -> str:
    """
    Determine the client's preferred locale from the Accept-Language header.
    If Spanish is preferred, return 'es'. Otherwise, return 'en'.
    If no preferred language is specified or the header is empty, return 'en' by default.
    """
    # Get the Accept-Language header (default to empty string if not present)
    accept_language = request.headers.get("Accept-Language", "")

    # If no Accept-Language header is provided, return 'en'
    if not accept_language:
        return "en"

    # Split the Accept-Language header by commas to get the list of preferred languages
    preferred_languages = accept_language.split(",")

    # Ensure the list is not empty
    if not preferred_languages or not preferred_languages[0]:
        return "en"

    # Take the first language in the list and strip any quality score if present
    most_preferred_language = preferred_languages[0].split(";")[
        0
    ]  # Strip any quality score if present

    # Return 'es' if the most preferred language is Spanish, otherwise 'en'
    if "es" in most_preferred_language.lower():
        return "es"

    return "en"


def get_message(messages: dict[str, dict[str, str]], key: str):
    """
    Get a translated message based on the client's locale.
    Falls back to English if the key doesn't exist in the preferred language.

    Args:
        messages: Dictionary containing translations
        key: The message key to look up

    Returns:
        Translated message string
    """
    locale = get_locale()

    # Get message from dictionary, fall back to English if not found
    if key in messages.get(locale, {}):
        return messages[locale][key]
    elif key in messages.get("en", {}):
        return messages["en"][key]
    else:
        # If message key doesn't exist anywhere, return the key itself
        return key
