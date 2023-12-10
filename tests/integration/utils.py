from odmantic.bson import ObjectId


def redact_objectid(s: str, oid: ObjectId) -> str:
    """Replace the ObjectId in a string with a placeholder."""
    return s.replace(str(oid), "<ObjectId>")
