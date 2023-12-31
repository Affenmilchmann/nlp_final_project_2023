from typing import List, Any, Dict, Optional
from stanza.models.common.doc import Sentence
import stanza
from pymorphy2 import MorphAnalyzer
import re
from fastapi import status, HTTPException

possible_pos_tags = {
    'ADJ',
    'ADP',
    'ADV',
    'AUX',
    'INTJ',
    'CCONJ',
    'NOUN',
    'DET',
    'PROPN',
    'NUM',
    'VERB',
    'PART',
    'PRON',
    'SCONJ',
    'SYM',
    'X'
}

morph = MorphAnalyzer()

def load_stanza() -> stanza.Pipeline:
    """Loads Stanza pipeline and returns it
    """
    return stanza.Pipeline(lang='ru', processors='tokenize,pos,lemma')

def get_text_sentences(text: str, pipeline: stanza.Pipeline) -> List[Dict[str, Any]]:
    """Tokenize and POS tag text using Stanza.

    Args:
        text (str): text to parse

    Returns:
        List[Sentence]: tokenized and POS tagged stanza sentences
    """
    doc = pipeline(text)
    return doc.to_dict()


def is_a_word(word: str) -> bool:
    """
    Returns true if word is not punctuation. Words like "как-то" are recognized as words, not punctuation.
    """
    return word.isalpha() or bool(re.match(r'[a-zA-Zа-яА-Я]+-?[a-zA-Zа-яА-Я]+', word))


def is_exact_form(word: str) -> bool:
    """
    Returns true if token is a request for an exact word form (a token in single or double quotes)
    """
    return bool(re.match(r'\".*\"|\'.*\'', word))


def is_pos_tag(word: str) -> bool:
    """
    Returns true if token is a CoNLL-U POS-tag
    """
    return word in possible_pos_tags


def parse_word(word: str) -> Dict[str, str]:
    """Parse a single word. It may be a wordform embedded in brackets or a lemma.

    Args:
        word (str): a word. word=walk(lemma),'walk'(wordform),"walk"(wordform)

    Raises:
        HTTPException: if given token is neither of lemma, pos-tag or word form requests

    Returns:
        Dict[str, str]: dict with a single key word_format: word.

    Example:
        parse_word("walk") -> {'lemma': 'walk'}

        parse_word("'walk'") -> {'word_form': 'walk'}

        parse_word('"walk"') -> {'word_form': 'walk'}

        parse_word('NOUN') -> {'pos': 'walk'}
    """
    if is_pos_tag(word):
        return {'pos': word}
    if is_exact_form(word):
        return {'word_form': re.sub(r'\'|\"', '', word.lower())}
    elif is_a_word(word):
        parsed = morph.parse(word)
        normal_forms = set([ p.normal_form.lower() for p in parsed ])
        return { 'lemma': list(normal_forms) }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Токен {word} не является ни леммой, ни pos-тегом, ни точной формой')


def parse_single_part(part: str) -> Dict[str, str]:
    """Parses single gram from ngram

    Args:
        part (str): an ngram part. Consists of a word and an optional pos tag separated by '+'
        
        Examples: камень; камень+NOUN; 'камень'; "камень"+VERB

    Raises:
        HTTPException: if more than one '+' found
        HTTPException: if first one is not a word or second one is not a POS tag

    Returns:
        Dict[str, str]: parsed part.

        Example: 
        
        "быть"+VERB ->  {'pos': 'VERB', 'word_form': 'быть'}

        делать -> {'lemma': 'делать'}
    """
    result = {}
    if '+' in part:
        subparts = part.split('+')
        if len(subparts) > 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Слишком много плюсов')
        if not ((is_a_word(subparts[0]) or is_exact_form(subparts[0])) and is_pos_tag(subparts[1])):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="""В случае запроса через плюс первая часть должна быть леммой или точной формой, 
                а вторая - pos-тегом""")
        result['pos'] = subparts[1]
        result.update(parse_word(subparts[0]))
    else:
        result.update(parse_word(part))
    return result


def request_to_trigram(request: str) -> Optional[Dict[int, str]]:
    """Parses raw ngram string.

    Args:
        request (str): raw ngram string

    Raises:
        HTTPException: if ngram has the size of more than 3 or less than 1

    Returns:
        Optional[Dict[int, str]]: parsed data

        Example:

        "быть"+VERB сильный 'человеком'+NOUN -> 
        `{1: {'pos': 'VERB', 'word_form': 'быть'}, 2: {'lemma': 'сильный'}, 3: {'pos': 'NOUN', 'word_form': 'человеком'}}`
    """
    requirements_for_tokens = {}
    search_parts = request.strip().split()
    if len(search_parts) > 3 or len(search_parts) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Принимаем от 1- до триграмм')
    
    for i, part in enumerate(search_parts):
        requirements_for_tokens[i+1] = parse_single_part(part)
    return requirements_for_tokens
