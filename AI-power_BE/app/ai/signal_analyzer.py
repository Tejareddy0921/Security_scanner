"""Small, explainable checks that complement the language model's verdict."""

from dataclasses import dataclass
from urllib.parse import urlsplit
import re


@dataclass(frozen=True)
class RiskFinding:
    key: str
    weight: float
    explanation: str
    recommendation: str
    scam_type: str | None = None


@dataclass(frozen=True)
class RiskAssessment:
    score: float
    findings: list[RiskFinding]


_CREDENTIAL_REQUEST = re.compile(
    r"\b(?:send|share|reply\s+with|provide|enter|confirm|verify|submit|tell\s+us)"
    r"\b.{0,70}\b(?:password|passcode|one[- ]time\s+(?:password|code|pin)|otp|"
    r"security\s+code|verification\s+code|recovery\s+code|pin\s+number|"
    r"card\s+(?:number|details)|bank\s+details)\b"
    r"|\b(?:password|passcode|one[- ]time\s+(?:password|code|pin)|otp|"
    r"security\s+code|verification\s+code|recovery\s+code|pin\s+number|"
    r"card\s+(?:number|details)|bank\s+details)\b.{0,70}"
    r"\b(?:send|share|reply\s+with|provide|enter|confirm|verify|submit)\b",
    re.IGNORECASE,
)
_PAYMENT_REQUEST = re.compile(
    r"\b(?:pay|send|transfer|wire|deposit|purchase|buy)\b.{0,70}"
    r"\b(?:gift\s+cards?|crypto(?:currency)?|bitcoin|wire\s+transfer|"
    r"cash\s+app|zelle|venmo|western\s+union|moneygram)\b"
    r"|\b(?:gift\s+cards?|crypto(?:currency)?|bitcoin|wire\s+transfer|"
    r"cash\s+app|zelle|venmo|western\s+union|moneygram)\b.{0,70}"
    r"\b(?:pay|send|transfer|wire|deposit|purchase|buy)\b",
    re.IGNORECASE,
)
_REMOTE_ACCESS_REQUEST = re.compile(
    r"\b(?:install|download|open|run|grant|allow|enable)\b.{0,70}"
    r"\b(?:anydesk|teamviewer|remote\s+access|screen\s+sharing|remote\s+control)\b"
    r"|\b(?:anydesk|teamviewer|remote\s+access|screen\s+sharing|remote\s+control)"
    r"\b.{0,70}\b(?:install|download|open|run|grant|allow|enable)\b",
    re.IGNORECASE,
)
_URGENCY = re.compile(
    r"\b(?:act\s+now|immediately|urgent|final\s+(?:notice|warning)|"
    r"expires?\s+(?:today|soon|in\s+\d+)|within\s+\d+\s*(?:minutes?|hours?|days?)|"
    r"right\s+away|limited\s+time|last\s+chance|before\s+(?:your\s+)?account\s+is\s+"
    r"(?:closed|suspended|locked))\b",
    re.IGNORECASE,
)
_THREAT = re.compile(
    r"\b(?:arrest\s+warrant|warrant\s+for\s+your\s+arrest|arrested\s+"
    r"(?:today|immediately)|legal\s+action\s+(?:will\s+be\s+taken\s+)?against\s+you|"
    r"lawsuit\s+against\s+you|deportation|account\s+(?:will\s+be\s+)?"
    r"(?:closed|suspended|locked)|service\s+will\s+be\s+disconnected)\b",
    re.IGNORECASE,
)
_PRIZE_OR_RETURN = re.compile(
    r"\b(?:you(?:'|’)ve\s+won|winner|claim\s+(?:your\s+)?prize|lottery|"
    r"guaranteed\s+(?:profit|return)|risk[- ]free\s+(?:investment|return)|"
    r"double\s+your\s+money)\b",
    re.IGNORECASE,
)
_URL = re.compile(r"\b(?:https?://|www\.)[^\s<>\[\]{}\"']+", re.IGNORECASE)
_SHORTENER_HOSTS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "cutt.ly",
    "is.gd",
    "rb.gy",
    "ow.ly",
    "shorturl.at",
}
_NEGATED_CREDENTIAL_REQUEST = re.compile(
    r"\b(?:never|don't|do\s+not|shouldn't|should\s+not|will\s+not|won't)\s+"
    r"(?:ever\s+)?(?:share|send|give|provide|tell|enter|reply\s+with)|"
    r"\b(?:will\s+never|never)\s+ask\s+(?:you\s+)?(?:for|to\s+share|to\s+send)",
    re.IGNORECASE,
)


def _has_active_credential_request(text: str) -> bool:
    for match in _CREDENTIAL_REQUEST.finditer(text):
        # Limit negation checks to the same clause, so a safety warning earlier
        # in a pasted conversation cannot hide a later request for a code.
        clause_start = max(text.rfind(mark, 0, match.start()) for mark in ".!?;:\n") + 1
        clause = text[clause_start : match.end()]
        if not _NEGATED_CREDENTIAL_REQUEST.search(clause):
            return True
    return False


class ScamSignalAnalyzer:
    """Detect a few high-signal social-engineering patterns without external data."""

    def analyze(self, content: str) -> RiskAssessment:
        text = " ".join(content.split())
        findings: list[RiskFinding] = []

        # Educational warnings such as "never share your OTP" should not count as
        # a request for credentials.
        if _has_active_credential_request(text):
            findings.append(
                RiskFinding(
                    "credentials",
                    0.48,
                    "The message asks for a password, one-time code, or sensitive financial details.",
                    "Never share passwords or one-time codes. Contact the organization through its official app or website.",
                    "phishing",
                )
            )

        if _PAYMENT_REQUEST.search(text):
            findings.append(
                RiskFinding(
                    "unusual_payment",
                    0.42,
                    "The message requests payment through a method often used to make transfers hard to reverse.",
                    "Do not send money or gift cards until you verify the request using a trusted contact method.",
                    "payment fraud",
                )
            )

        if _REMOTE_ACCESS_REQUEST.search(text):
            findings.append(
                RiskFinding(
                    "remote_access",
                    0.42,
                    "The message asks you to install remote-access software or share control of your device.",
                    "Do not install remote-access software or grant screen control to an unsolicited contact.",
                    "tech support scam",
                )
            )

        if _PRIZE_OR_RETURN.search(text):
            findings.append(
                RiskFinding(
                    "unexpected_reward",
                    0.24,
                    "The message promises an unexpected prize or guaranteed financial return.",
                    "Treat unexpected prizes and guaranteed returns cautiously; do not pay a fee to claim them.",
                    "advance-fee fraud",
                )
            )

        if _URGENCY.search(text):
            findings.append(
                RiskFinding(
                    "urgency",
                    0.16,
                    "The message pressures you to act quickly or threatens a near-term consequence.",
                    "Pause and verify the claim independently before taking action.",
                )
            )

        if _THREAT.search(text):
            findings.append(
                RiskFinding(
                    "threat_or_impersonation",
                    0.20,
                    "The message uses a threat or account consequence to pressure you.",
                    "Do not use contact details in the message; find the official organization contact yourself.",
                    "impersonation",
                )
            )

        for raw_url in _URL.findall(text):
            candidate = raw_url.rstrip(".,!?;:)")
            normalized = candidate if "://" in candidate else f"https://{candidate}"
            try:
                host = (urlsplit(normalized).hostname or "").lower().rstrip(".")
            except ValueError:
                host = ""
            if host and any(host == shortener or host.endswith(f".{shortener}") for shortener in _SHORTENER_HOSTS):
                findings.append(
                    RiskFinding(
                        "shortened_link",
                        0.20,
                        "The message contains a shortened link that hides its destination.",
                        "Avoid opening shortened links in unexpected messages; visit the official site directly.",
                        "phishing",
                    )
                )
                break

        # Combine independent evidence while keeping the score bounded. This is
        # an evidence score, not a claim of calibrated probability.
        score = 1.0
        for finding in findings:
            score *= 1.0 - finding.weight
        return RiskAssessment(score=round(1.0 - score, 3), findings=findings)
