from dataclasses import dataclass
from typing import Tuple, Optional, List

@dataclass
class Token:
    text_position: Tuple[int, int]
    sentence: int
    wordform: int
    lemma: int
    pos_tag: int

    def __eq__(self, __value) -> bool:
        if __value == None: return False
        if not isinstance(__value, Token): raise TypeError("Compared value must be the same type.")
        return self.wordform == __value.wordform and \
                self.lemma == __value.lemma and \
                self.pos_tag == __value.pos_tag and \
                self.text_position == __value.text_position

    def __str__(self):
        return f"'{self.wordform}' ({self.lemma}, {self.pos_tag}), {self.text_position}"

class Trigram:
    def __init__(self, trigram: Tuple[Token, Token, Token]) -> None:
        if trigram[0] == trigram[1] == trigram[2] == None:
            raise ValueError("Trigram cannot contain all None")
        self.trigram = trigram

        first_not_none = 0
        while trigram[first_not_none] == None: first_not_none += 1
        last_not_none = 2
        while trigram[last_not_none] == None: last_not_none -= 1

        self.text_position = (
            trigram[first_not_none].text_position[0], 
            trigram[last_not_none].text_position[1]
        )

    def __getitem__(self, key):
        return self.trigram[key]

    def __eq__(self, __value) -> bool:
        if __value == None: return False
        if not isinstance(__value, Trigram): raise TypeError("Compared value must be the same type.")
        return self[0] == __value[0] and \
                self[1] == __value[1] and \
                self[2] == __value[2] and \
                self.text_position == __value.text_position

    def __str__(self) -> str:
        def short_token_str(token: Token) -> str:
            if not token: return "-"
            return f"'{token.wordform}'({token.pos_tag.upper()})"
        return f"[{short_token_str(self[0])}, {short_token_str(self[1])}, {short_token_str(self[2])}]{self.text_position}"


class LocalTrigram:

    def __init__(self, token_1: Optional[Token] = None, token_2: Optional[Token] = None, token_3: Optional[Token] = None):
        self.token_1, self.token_2, self.token_3 = token_1, token_2, token_3

    def move(self):
        self.token_1, self.token_2, self.token_3 = self.token_2, self.token_3, None

