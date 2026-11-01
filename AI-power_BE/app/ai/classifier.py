from app.ai.groq_service import GroqService
from app.ai.prompt_service import PromptService
from app.ai.rag_service import RAGService
from app.ai.signal_analyzer import RiskAssessment, ScamSignalAnalyzer
from app.models.detection_result import ScamLabel
from app.schemas.detection import AIResult


class ScamClassifier:
    def __init__(
        self,
        llm: GroqService,
        prompt: PromptService | None = None,
        rag: RAGService | None = None,
        signal_analyzer: ScamSignalAnalyzer | None = None,
    ) -> None:
        self.llm = llm
        self.prompt = prompt or PromptService()
        self.rag = rag or RAGService()
        self.signal_analyzer = signal_analyzer or ScamSignalAnalyzer()

    async def classify(self, content: str) -> AIResult:
        assessment = self.signal_analyzer.analyze(content)
        context = await self.rag.retrieve_context(content)
        messages = self.prompt.build_messages(content, context)
        model_result = await self.llm.classify(messages)
        return self._combine(model_result, assessment)

    @staticmethod
    def _combine(model_result: AIResult, assessment: RiskAssessment) -> AIResult:
        """Keep the model's assessment unless independent evidence raises risk."""
        score = assessment.score
        label = model_result.label
        if score >= 0.63:
            label = ScamLabel.scam
        elif score >= 0.36 and label == ScamLabel.not_scam:
            label = ScamLabel.suspicious

        findings = assessment.findings
        risk_factors = []
        seen_factors = set()
        for value in [*(finding.explanation for finding in findings), *model_result.risk_factors]:
            key = value.casefold()
            if key not in seen_factors:
                seen_factors.add(key)
                risk_factors.append(value)

        recommendations = []
        seen_recommendations = set()
        for value in [*(finding.recommendation for finding in findings), *model_result.recommendations]:
            key = value.casefold()
            if key not in seen_recommendations:
                seen_recommendations.add(key)
                recommendations.append(value)

        explanation = model_result.explanation
        if findings:
            finding_summary = "; ".join(finding.explanation for finding in findings)
            if label != model_result.label:
                explanation = f"Independent checks raised the risk: {finding_summary} Model assessment: {explanation}"
            else:
                explanation = f"{explanation} Independent checks also found: {finding_summary}"
        explanation = explanation[:2_000].rstrip()

        # A rule-triggered change replaces the model's confidence in its original
        # label with a conservative evidence score for the raised-risk result.
        confidence = model_result.confidence_score
        if label != model_result.label:
            confidence = max(score, 0.55 if label == ScamLabel.suspicious else 0.63)

        scam_type = model_result.scam_type
        if scam_type is None and findings:
            strongest = max(findings, key=lambda finding: finding.weight)
            scam_type = strongest.scam_type

        return AIResult(
            label=label,
            confidence_score=round(confidence, 3),
            scam_type=scam_type,
            risk_factors=risk_factors[:20],
            recommendations=recommendations[:20],
            explanation=explanation,
        )
