from pydantic import EmailStr


def mask_email(email: EmailStr) -> EmailStr:
    """Mask email address for privacy."""
    local, domain = email.split("@", 1)

    if len(local) <= 2:
        masked_local = local
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def normalize_email(email: EmailStr) -> EmailStr:
    """Normalize email address for consistent storage and duplicate detection."""
    normalized = email.lower().strip()

    local_part, domain = normalized.rsplit("@", 1)
    if "+" in local_part:
        local_part = local_part.split("+")[0]

    # Domain-specific normalization
    if domain in ["gmail.com", "googlemail.com"]:
        local_part = local_part.replace(".", "")  # Remove dots Gmail ignores them
        domain = "gmail.com"  # Normalize googlemail.com to gmail.com

    return f"{local_part}@{domain}"
