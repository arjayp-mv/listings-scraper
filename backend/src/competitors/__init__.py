# =============================================================================
# Competitors Domain Module
# =============================================================================
# Purpose: Competitor tracking and research for Amazon products
# Public API: router, service
# =============================================================================

from .router import router
from .service import CompetitorService

__all__ = ["router", "CompetitorService"]
