"""Pydantic schema definitions for Composio Toolkit Research.

Every factual field encapsulates:
- value
- evidence_url
- evidence_quote (verbatim quote from source documentation)
- confidence ('high' | 'medium' | 'low')
"""

from typing import Generic, List, Literal, Optional, TypeVar, Any, Dict
from pydantic import BaseModel, Field

T = TypeVar("T")

ConfidenceLevel = Literal["high", "medium", "low"]

AppType = Literal["hosted_saas", "self_hosted_oss", "cli_tool", "unclear"]
AuthMethod = Literal[
    "oauth2",
    "api_key",
    "basic",
    "bearer_token",
    "hmac_signature",
    "jwt",
    "session_cookie",
    "none",
    "other",
]
OAuthFlow = Literal["auth_code", "client_credentials", "pkce", "device", "n/a"]
AccessModel = Literal[
    "self_serve_free",
    "self_serve_trial",
    "paid_plan_required",
    "app_review_required",
    "admin_approval",
    "partner_gated",
    "contact_sales",
    "not_applicable",
]
ApiType = Literal[
    "rest", "graphql", "soap", "websocket", "sdk_only", "cli_only", "none"
]
ApiBreadth = Literal["narrow", "medium", "broad", "unknown"]
YesNoUnknown = Literal["yes", "no", "unknown"]
ExistingMcpType = Literal["official", "community", "none"]
Buildability = Literal["green", "yellow", "red"]
MainBlocker = Literal[
    "app_review",
    "paid_plan",
    "partner_program",
    "contact_sales",
    "no_public_api",
    "cli_or_local_only",
    "self_hosted_per_instance",
    "complex_request_signing",
    "kyc_or_regional",
    "thin_or_unclear_docs",
    "enterprise_only",
    "waitlist",
    "none",
]


class Fact(BaseModel, Generic[T]):
    value: T
    evidence_url: str = Field(default="unknown", description="Source documentation URL")
    evidence_quote: str = Field(
        default="unknown", description="Verbatim quote from source docs"
    )
    confidence: ConfidenceLevel = Field(
        default="medium", description="Confidence in this assertion"
    )


class AuthMethodsFact(Fact[List[AuthMethod]]):
    note: Optional[str] = Field(
        default=None, description="Additional notes regarding authentication methods"
    )


class ApiBreadthFact(Fact[ApiBreadth]):
    endpoint_count: Optional[int] = Field(
        default=None, description="Documented count of endpoints if known"
    )


class OpenApiSpecFact(Fact[YesNoUnknown]):
    spec_url: Optional[str] = Field(
        default=None, description="URL pointing directly to OpenAPI / Swagger spec"
    )


class ExistingMcpFact(Fact[ExistingMcpType]):
    mcp_url: Optional[str] = Field(
        default=None, description="Repository or documentation URL for existing MCP server"
    )


class EstimatedToolCountFact(BaseModel):
    value: int = Field(default=0, description="Estimated count of tools for an agent toolkit")
    basis: str = Field(default="Estimated based on core API endpoint surface", description="Rationale for tool count estimate")
    confidence: ConfidenceLevel = Field(default="medium")


class AppResearchRecord(BaseModel):
    id: int = Field(..., description="App ID from Appendix A (1-100)")
    name: str = Field(..., description="Application name")
    category: Fact[str] = Field(..., description="App category")
    one_liner: Fact[str] = Field(..., description="One-line summary of what it does")
    app_type: Fact[AppType] = Field(..., description="Hosting/distribution model")
    auth_methods: AuthMethodsFact = Field(..., description="Supported auth methods")
    oauth_flows: Fact[List[OAuthFlow]] = Field(..., description="Supported OAuth flows")
    access_model: Fact[AccessModel] = Field(..., description="Credential self-serve vs gating")
    api_type: Fact[List[ApiType]] = Field(..., description="Supported API paradigms")
    api_breadth: ApiBreadthFact = Field(..., description="API breadth and scope")
    openapi_spec: OpenApiSpecFact = Field(..., description="Availability of OpenAPI spec")
    webhooks_triggers: Fact[YesNoUnknown] = Field(..., description="Webhook / event trigger support")
    sandbox: Fact[YesNoUnknown] = Field(..., description="Sandbox or test environment availability")
    rate_limits: Fact[str] = Field(..., description="Documented rate limit details or unknown")
    existing_mcp: ExistingMcpFact = Field(..., description="Existing MCP servers (official/community/none)")
    already_in_composio: Fact[YesNoUnknown] = Field(..., description="Whether Composio already has a toolkit")
    buildability: Fact[Buildability] = Field(..., description="Green, yellow, or red buildability verdict")
    main_blocker: Fact[MainBlocker] = Field(..., description="Primary blocker if not green or if gating exists")
    estimated_tool_count: EstimatedToolCountFact = Field(..., description="Estimated tool count")
    reasoning: str = Field(..., description="1-2 sentences explaining buildability verdict and developer vs managed app distinction")
    overall_confidence: ConfidenceLevel = Field(..., description="Overall confidence level")

    def to_flat_dict(self) -> Dict[str, Any]:
        """Flatten record for CSV and HTML table consumption."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "one_liner": self.one_liner.value,
            "app_type": self.app_type.value,
            "auth_methods": ",".join(self.auth_methods.value) if isinstance(self.auth_methods.value, list) else str(self.auth_methods.value),
            "auth_methods_note": self.auth_methods.note or "",
            "oauth_flows": ",".join(self.oauth_flows.value) if isinstance(self.oauth_flows.value, list) else str(self.oauth_flows.value),
            "access_model": self.access_model.value,
            "api_type": ",".join(self.api_type.value) if isinstance(self.api_type.value, list) else str(self.api_type.value),
            "api_breadth": self.api_breadth.value,
            "endpoint_count": self.api_breadth.endpoint_count or "",
            "openapi_spec": self.openapi_spec.value,
            "openapi_spec_url": self.openapi_spec.spec_url or "",
            "webhooks_triggers": self.webhooks_triggers.value,
            "sandbox": self.sandbox.value,
            "rate_limits": self.rate_limits.value,
            "existing_mcp": self.existing_mcp.value,
            "existing_mcp_url": self.existing_mcp.mcp_url or "",
            "already_in_composio": self.already_in_composio.value,
            "buildability": self.buildability.value,
            "main_blocker": self.main_blocker.value,
            "estimated_tool_count": self.estimated_tool_count.value,
            "tool_count_basis": self.estimated_tool_count.basis,
            "reasoning": self.reasoning,
            "overall_confidence": self.overall_confidence,
            "evidence_auth_url": self.auth_methods.evidence_url,
            "evidence_auth_quote": self.auth_methods.evidence_quote,
            "evidence_access_url": self.access_model.evidence_url,
            "evidence_access_quote": self.access_model.evidence_quote,
            "evidence_buildability_url": self.buildability.evidence_url,
            "evidence_buildability_quote": self.buildability.evidence_quote,
        }
