CLAUDE_TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": (
            "Search the internal knowledge base for cached drug pricing data and state Medicaid "
            "PBM audit findings. Always call this FIRST before fetching fresh data. "
            "Returns None if no recent data found (older than max_age_days)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Drug name, drug class, or topic to search for"
                },
                "max_age_days": {
                    "type": "integer",
                    "default": 7,
                    "description": "Maximum age of cached data in days"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_nadac_baseline",
        "description": (
            "Fetch the NADAC (National Average Drug Acquisition Cost) from CMS — "
            "the true acquisition cost pharmacies pay. This is the pass-through pricing benchmark. "
            "Returns per-unit price and total for the specified quantity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string",
                    "description": "Brand or generic drug name"
                },
                "ndc": {
                    "type": "string",
                    "description": "NDC code if known (more precise)"
                },
                "quantity": {
                    "type": "integer",
                    "default": 30,
                    "description": "Prescription quantity (e.g. 30, 60, 90)"
                }
            },
            "required": ["drug_name"]
        }
    },
    {
        "name": "search_drug_prices",
        "description": (
            "Search current drug prices across GoodRx and PBM formularies using parallel web agents. "
            "Returns lowest prices found per source. Takes 30-60 seconds to complete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string",
                    "description": "Brand or generic drug name"
                },
                "strength": {
                    "type": "string",
                    "description": "Dose strength, e.g. '5mg', '10/40mg'"
                },
                "quantity": {
                    "type": "integer",
                    "default": 30
                },
                "pbm_target": {
                    "type": "string",
                    "enum": ["CVS_Caremark", "Express_Scripts", "OptumRx", "all"],
                    "default": "all"
                }
            },
            "required": ["drug_name"]
        }
    },
    {
        "name": "create_monitoring_task",
        "description": (
            "Create a recurring price monitoring workflow for a drug. "
            "The system will check for price changes on the specified schedule and alert the user."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string"
                },
                "frequency": {
                    "type": "string",
                    "enum": ["daily", "weekly", "biweekly", "monthly"],
                    "default": "weekly"
                }
            },
            "required": ["drug_name"]
        }
    },
    {
        "name": "generate_discrepancy_report",
        "description": (
            "Generate a structured discrepancy report from collected pricing data. "
            "Call this after you have NADAC and market pricing data. "
            "Calculates spread, flags discrepancies, adds Medicaid citations, and saves to knowledge base."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "drugs": {
                    "type": "array",
                    "description": "List of drug pricing objects with nadac_per_unit, plan_price, etc.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "strength": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "nadac_per_unit": {"type": "number"},
                            "plan_price": {"type": "number"},
                            "goodrx_lowest": {"type": "number"},
                            "ndc": {"type": "string"}
                        },
                        "required": ["drug_name", "nadac_per_unit"]
                    }
                },
                "query": {
                    "type": "string",
                    "description": "Original user query for context"
                }
            },
            "required": ["drugs", "query"]
        }
    }
]
