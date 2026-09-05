from app.core.prompts import HUMANIZE_PROMPT
from app.services.detector import Detector
from app.services.llm import generate

class Humanizer:

    def __init__(self): 
        self.detector = Detector()

    async def rewrite(self, text: str):

        before = await self.detector.score(text)

        rewritten = await generate(
            HUMANIZE_PROMPT.format(text=text)
        )

        after = await self.detector.score(rewritten)

        return {
            "original": text,
            "rewritten": rewritten,
            "score_before": before,
            "score_after": after
        }
