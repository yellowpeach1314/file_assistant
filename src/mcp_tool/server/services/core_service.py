from src.ai_retrieval import Retriever
from src.norms_checker import NormsChecker

class CoreService:
    def __init__(self):
        self.retriever = Retriever()
        self.validator = NormsChecker()

    def process(self, payload):
        # 集成现有模块功能
        docs = self.retriever.retrieve(payload.query)
        validated = self.validator.check(docs)
        return {
            "documents": validated,
            "analysis": self._generate_insights(validated)
        }