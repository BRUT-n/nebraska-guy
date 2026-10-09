from string import ascii_letters, digits


def is_valid_package_name(name: str) -> tuple[bool, str]:
    """
    Проверяет имя пакета по стандарту PEP 508.
    """
    if not (1 <= len(name) <= 214):
        return False, "имя пакета должно быть от 1 до 214 символов"

    ascii_nums = set(ascii_letters + digits)
    allowed_extra = {".", "-", "_"}

    if name[0] not in ascii_nums:
        return False, "имя пакета должно начинаться с буквы или цифры"
    if name[-1] not in ascii_nums:
        return False, "имя пакета должно заканчиваться буквой или цифрой"

    for ch in name:
        if ch not in ascii_nums and ch not in allowed_extra:
            return False, f"Недопустипый символ в имени пакета {ch!r}"

    return True, ""


def normalize_package_name(name: str) -> str:
    """
    Нормализирует имя пакета по PEP 503.
    """
    normalized_name = name.lower().replace(".", "-").replace("_", "-")

    while "--" in normalized_name:
        normalized_name = normalized_name.replace("--", "-")

    return normalized_name
