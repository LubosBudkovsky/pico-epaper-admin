def normalize_name(text):
    """Slugify text into a lowercase alphanumeric+underscore name."""
    s = text.lower()
    result = []
    prev_under = False
    for c in s:
        if c.isalpha() or c.isdigit():
            result.append(c)
            prev_under = False
        else:
            if not prev_under and result:
                result.append("_")
            prev_under = True
    return "".join(result).strip("_")
