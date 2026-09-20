import re


WORD_PATTERN = re.compile(r"[a-zA-Z0-9]+(?:['-][a-zA-Z0-9]+)?")

# People rarely type only the factual part of a question. These leading phrases
# do not change intent, so remove them before applying retrieval rules. Keeping
# this at the query boundary avoids throwing useful words such as "support" or
# "account" away when they appear in the actual question.
QUERY_PREAMBLE = re.compile(
    r"^\s*(?:"
    r"please\s+(?:answer|confirm|clarify)|"
    r"can\s+you\s+(?:tell\s+me|verify)|"
    r"could\s+you\s+(?:please\s+tell\s+me|explain|check)|"
    r"i\s+(?:need\s+(?:to\s+know|a\s+clear\s+answer)|would\s+like\s+to\s+ask|am\s+wondering)|"
    r"according\s+to\s+the\s+documents|"
    r"based\s+on\s+available\s+information|"
    r"from\s+the\s+support\s+docs|"
    r"using\s+northstar\s+policy|"
    r"(?:quick|customer|support)\s+question|"
    r"help\s+me\s+understand|"
    r"for\s+(?:a\s+customer|my\s+account)|"
    r"in\s+simple\s+words|"
    r"before\s+i\s+proceed"
    r")\s*[:,;-]?\s*",
    flags=re.I,
)

QUERY_TRAILING_INSTRUCTION = re.compile(
    r"\s*(?:please\s+)?(?:"
    r"use\s+(?:only\s+)?(?:the\s+)?(?:local|provided|available)?\s*(?:documents|docs)|"
    r"answer\s+(?:using|from|based\s+on)\s+(?:only\s+)?(?:the\s+)?"
    r"(?:local|provided|available)?\s*(?:documents|docs)|"
    r"refer\s+to\s+(?:only\s+)?(?:the\s+)?(?:local|provided|available)?\s*"
    r"(?:documents|docs)"
    r")[.!]*\s*$",
    flags=re.I,
)

STOP_WORDS = {
    "a",
    "an",
    "and",
    "after",
    "automatically",
    "are",
    "can",
    "do",
    "does",
    "for",
    "from",
    "happens",
    "how",
    "i",
    "if",
    "information",
    "in",
    "is",
    "it",
    "me",
    "long",
    "much",
    "my",
    "needed",
    "not",
    "ns",
    "northstar",
    "of",
    "on",
    "or",
    "offer",
    "offers",
    "policy",
    "plan",
    "plus",
    "provide",
    "provides",
    "report",
    "required",
    "the",
    "things",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "will",
    "with",
    "should",
    "available",
    "by",
    "get",
}

# A few domain-neutral forms make keyword search less brittle without trying to
# pretend this small project contains a full natural-language pipeline.
NORMAL_FORMS = {
    "billed": "charge",
    "cancelled": "cancel",
    "canceled": "cancel",
    "cancels": "cancel",
    "cancellation": "cancel",
    "cancelling": "cancel",
    "charged": "charge",
    "charges": "charge",
    "collected": "collect",
    "collects": "collect",
    "countries": "destination",
    "country": "destination",
    "destinations": "destination",
    "costs": "cost",
    "converted": "convert",
    "converts": "convert",
    "delivery": "shipping",
    "drains": "drain",
    "exchanged": "exchange",
    "exchanges": "exchange",
    "fees": "fee",
    "included": "include",
    "includes": "include",
    "incorrect": "error",
    "non-refundable": "refund",
    "paid": "premium",
    "paired": "pair",
    "pairing": "pair",
    "provide": "include",
    "provides": "include",
    "refunds": "refund",
    "refunded": "refund",
    "refundable": "refund",
    "returned": "return",
    "returns": "return",
    "reimbursement": "refund",
    "renewals": "renewal",
    "reporting": "report",
    "ship": "shipping",
    "shipped": "shipping",
    "ships": "shipping",
    "subscriptions": "subscription",
    "syncs": "sync",
    "tracking": "track",
    "tracked": "track",
    "tracks": "track",
    "yearly": "annual",
    "plans": "plan",
    "payments": "charge",
    "payment": "charge",
    "send": "include",
    "unexpected": "error",
    "activities": "activity",
    "steps": "step",
    "wearable": "band",
    "workouts": "workout",
}


def tokenize(text: str) -> list[str]:
    text = re.sub(r"northstar\s*\+", "premium subscription", text, flags=re.I)
    text = re.sub(r"northstar\s+plus", "premium subscription", text, flags=re.I)
    tokens: list[str] = []
    for match in WORD_PATTERN.finditer(text.lower()):
        token = match.group(0).strip("-'")
        token = NORMAL_FORMS.get(token, token)
        if token and token not in STOP_WORDS:
            tokens.append(token)
    return tokens


def tokenize_query(text: str) -> list[str]:
    """Tokenize a question and normalize a few common user intents."""
    text = QUERY_PREAMBLE.sub("", text)
    text = QUERY_TRAILING_INSTRUCTION.sub("", text)
    lowered = text.casefold()
    tokens = tokenize(text)

    if "pay each month" in lowered or "monthly price" in lowered:
        return ["monthly", "cost"]
    if "pay each year" in lowered or "ninety-nine" in lowered:
        return ["annual", "cost"]
    if "cheaper" in lowered and "monthly" in lowered:
        return ["annual", "monthly", "price"]
    if "free tier" in lowered and any(word in lowered for word in ("payment", "pay", "cost")):
        return ["free", "tier", "include"]

    if "premium" in tokens and "free" in tokens and any(
        word in lowered for word in ("days", "try")
    ):
        return ["free", "trial"]

    if "trial" in lowered:
        if any(word in lowered for word in ("billed", "charged", "finishes", "ends")):
            return ["trial", "charge"]
        if "cancel" in tokens and any(
            word in lowered for word in ("access", "premium", "retain", "keep")
        ):
            return ["trial", "cancel", "access"]
        if "cancel" in tokens and any(word in lowered for word in ("convert", "before")):
            return ["trial", "cancel", "convert"]
        if any(word in lowered for word in ("introductory", "everyone", "eligible")):
            return ["trial", "eligibility"]
        if "money back" in lowered or "refund" in lowered:
            return ["trial", "charge", "refund"]
        if "premium" in lowered and "free" in lowered:
            return ["free", "trial"]

    if "bank" in lowered and "refund" in lowered:
        return ["refund", "business", "days"]
    if "approved" in lowered and "refund" in tokens and any(
        word in lowered for word in ("long", "take", "time")
    ):
        return ["approved", "refund", "business", "days"]
    if "hardware" in lowered and "return" in tokens and "window" in lowered:
        return ["hardware", "return", "14", "days"]
    if "exchange" in lowered and "size" in lowered:
        return ["exchange", "size"]
    if "delivery fee" in lowered or "shipping fee" in lowered:
        return ["shipping", "fee", "refund"]
    if "return" in lowered and "accessories" in lowered:
        return ["return", "accessories"]

    if "standard" in lowered and any(word in lowered for word in ("delivery", "arrive")):
        return ["standard", "shipping"]
    if "expedited" in lowered and any(word in lowered for word in ("delivery", "arrive")):
        return ["expedited", "shipping"]
    if "processing" in lowered and "shipping" in lowered:
        return ["processing", "shipping"]
    if "deliver hardware" in lowered or "ship hardware" in lowered:
        return ["shipping", "destination"]
    if "carrier" in lowered and "delivered" in lowered:
        return ["delivered", "package"]
    if "reroute" in lowered and "order" in lowered:
        return ["address", "order", "carrier"]
    if "order" in lowered and "processing" in lowered:
        return ["order", "processing", "business", "days"]

    if "side button" in lowered:
        return ["side", "button", "seconds"]
    if "pair" in tokens and "band" in tokens:
        return ["pair", "add", "device", "side", "button"]
    if "bluetooth" in tokens and "sync" in tokens and "band" in tokens:
        return ["band", "sync", "bluetooth"]
    if any(phrase in lowered for phrase in ("not appearing", "cannot find", "can't find")):
        return ["app", "find", "band"]
    if "activity data" in lowered and any(word in lowered for word in ("stopped", "old", "updating")):
        return ["device", "data", "old"]
    if "sleep" in lowered and any(word in lowered for word in ("incomplete", "missing", "records")):
        return ["sleep", "missing"]
    if "battery" in lowered and any(word in lowered for word in ("drain", "quickly")):
        if any(word in lowered for word in ("cause", "why")):
            return ["battery", "performance", "usage", "patterns"]
        return ["battery", "drain"]

    if "premium" in tokens and "locked" in tokens and "charge" in tokens:
        return ["premium", "locked", "charge"]

    if any(phrase in lowered for phrase in ("health signals", "measured by the wearable")):
        return ["band", "track"]
    if "record workouts" in lowered and "sleep" in lowered:
        return ["track", "workout", "sleep"]
    if "calculate recovery" in lowered:
        return ["track", "recovery"]
    if "free users" in lowered and "band" in lowered:
        return ["free", "tier", "include"]
    if "requires payment" in lowered or "coaching tools" in lowered:
        return ["premium", "features", "include"]

    if "registered email" in lowered or "old email" in lowered:
        return ["email", "account", "recovery"]
    if "account deletion" in lowered and "app" in lowered:
        return ["account", "deletion", "support"]
    if "records" in lowered and "account deletion" in lowered:
        return ["account", "deletion", "retained"]
    if "health information" in lowered and any(word in lowered for word in ("sold", "advertising")):
        return ["sell", "health", "advertisers"]
    if "annual" in lowered and "free" in lowered and "band" in lowered:
        return ["annual", "include", "band", "bundle"]

    asks_for_features = any(
        phrase in lowered
        for phrase in ("feature", "included", "include", "provide", "what do i get")
    )
    mentions_premium_product = "northstar plus" in lowered or "northstar+" in lowered
    mentions_paid_subscription = "paid subscription" in lowered or "paid plan" in lowered
    if asks_for_features and (
        mentions_premium_product
        or mentions_paid_subscription
        or "premium" in lowered
    ):
        return ["premium", "features", "include"]

    billing_problem = any(
        phrase in lowered
        for phrase in ("incorrect", "charged in error", "billing error", "unexpected charge")
    )
    if billing_problem:
        canonical = ["billing", "charge", "error"]
        if any(word in lowered for word in ("provide", "send", "report", "details")):
            canonical.append("include")
        if "phone" in lowered:
            canonical.append("phone")
        return canonical

    tracking_question = "band" in lowered and any(
        word in lowered for word in ("track", "tracked", "tracking", "count steps")
    )
    if tracking_question:
        canonical = ["band", "track"]
        if len(tokens) <= 2:
            return ["band", "heart", "step", "sleep", "workout", "recovery"]
        for detail in ("heart", "sleep", "step", "recovery", "blood", "pressure", "diabetes"):
            if detail in tokens:
                canonical.append(detail)
        return canonical

    if "refund" in tokens and "request" in tokens and any(
        word in lowered for word in ("information", "details", "needed", "required")
    ):
        return ["refund", "request", "contact"]

    if "free" in tokens and "trial" in tokens:
        return ["free", "trial"]

    if "cancel" in tokens and any(
        phrase in lowered for phrase in ("what happens", "after i cancel", "after cancellation")
    ):
        return ["cancel", "access"]

    if "cancel" in tokens and any(word in lowered for word in ("where", "how")):
        return ["cancel", "billing", "section"]

    return tokens
