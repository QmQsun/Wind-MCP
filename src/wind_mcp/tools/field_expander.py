"""
Expands FieldSet shortcuts in user-provided field lists.

Logic:
1. If a field name is ALL_CAPS and exists in FIELDSETS, expand it
2. Otherwise, pass through as a raw Wind field name
3. Deduplicate while preserving order
"""

from .fieldsets import FIELDSETS, get_screening_full


def expand_fields(fields: str | list[str]) -> list[str]:
    """
    Expand field list, resolving any FieldSet shortcuts.

    Args:
        fields: Comma-separated string or list of field names / FieldSet names.

    Returns:
        Flat list of Wind field mnemonics (deduplicated).
    """
    if isinstance(fields, str):
        raw_list = [f.strip() for f in fields.split(",")]
    else:
        raw_list = fields

    expanded = []
    for item in raw_list:
        item_stripped = item.strip()
        upper = item_stripped.upper()

        if upper == "SCREENING_FULL":
            expanded.extend(get_screening_full())
        elif upper in FIELDSETS and FIELDSETS[upper] is not None:
            expanded.extend(FIELDSETS[upper])
        else:
            # Raw Wind field name — pass through as-is
            expanded.append(item_stripped)

    # Deduplicate preserving order
    seen = set()
    result = []
    for f in expanded:
        key = f.lower()
        if key not in seen:
            seen.add(key)
            result.append(f)
    return result
