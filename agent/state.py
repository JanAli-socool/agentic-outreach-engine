"""Typed state passed between graph nodes. Single source of truth."""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class CompanyResearch(BaseModel):
    domain: str
    homepage_text: str = ""
    search_results: List[str] = Field(default_factory=list)
    scrape_failed: bool = False
    search_failed: bool = False


class ICPDecision(BaseModel):
    is_fit: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    matched_criteria: List[str] = Field(default_factory=list)
    missing_criteria: List[str] = Field(default_factory=list)


class EmailDraft(BaseModel):
    subject: str
    body: str
    personalization_hooks: List[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    passed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    grounded_claims: List[str] = Field(default_factory=list)


class AgentState(BaseModel):
    # Inputs
    company_domain: str
    icp_criteria: str

    # Pipeline outputs
    research: Optional[CompanyResearch] = None
    icp_decision: Optional[ICPDecision] = None
    email_draft: Optional[EmailDraft] = None
    verification: Optional[VerificationResult] = None

    # Control state
    retry_count: int = 0
    status: Literal["running", "not_fit", "completed", "failed"] = "running"
    error: Optional[str] = None
    trace: List[str] = Field(default_factory=list)

    def log(self, message: str) -> None:
        self.trace.append(message)