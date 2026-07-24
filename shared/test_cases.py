"""
Fixed list of test inputs used identically by all four agents,
so the comparison table is a fair, apples-to-apples comparison.
"""

from shared.data import CAMPAIGNS

# Index reference for the five scenarios:
# CAMPAIGNS[2] (camp_104) -> clearly healthy, all agents should agree: continue
# CAMPAIGNS[0] (camp_101) -> clearly bad (no conversions, low ROAS), all agents should agree: pause
# CAMPAIGNS[3] (camp_105) -> tricky: good CTR but high cost_per_conversion / low ROAS
# CAMPAIGNS[4] (camp_106) -> borderline: today's numbers look fine,
#                            but get_campaign_history shows 4 days declining —
#                            only Constrained ReAct should catch it via history

TEST_CASES = CAMPAIGNS