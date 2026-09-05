import random

class Detector:

    async def score(self, text: str):
        return round(random.uniform(20, 90), 2)