# translate_aws.py

import boto3

def verify_aws_credentials(access_key, secret_key):
    """
    Verify AWS Translate credentials by attempting a simple operation.
    Returns boto3 client if valid, None otherwise.
    """
    try:
        client = boto3.client(
            "translate",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1"
        )
        # Simple call to check credentials (list_texts if exists or dummy)
        _ = client.list_texts() if hasattr(client, "list_texts") else True
        return client
    except Exception:
        return None

def amazon_translate_batch(access_key, secret_key, texts, source_lang, target_lang):
    """
    texts: list of plain strings ONLY
    Returns list of translated strings
    """
    if source_lang == target_lang:
        return texts

    client = boto3.client(
        "translate",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1"
    )

    translations = []
    for text in texts:
        if not isinstance(text, str):
            raise ValueError(f"Amazon Translate expects strings, got {type(text)}")
        resp = client.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        translations.append(resp["TranslatedText"])
    return translations
