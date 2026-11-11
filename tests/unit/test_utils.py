import pytest
from src.models.utils import is_valid_package_name, normalize_package_name


@pytest.mark.parametrize(
    "name, expected_is_valid, expected_error_part",
    [
        ("requests", True, ""),
        ("w", True, ""),
        ("pydantic-core", True, ""),
        ("some_package", True, ""),
        ("some.package", True, ""),
        ("some-package-1", True, ""),
        ("s" * 214, True, ""),
        ("", False, "имя пакета должно быть от 1 до 214 символов"),
        ("s" * 215, False, "имя пакета должно быть от 1 до 214 символов"),
        ("some package", False, "Недопустимый символ в имени пакета ' '"),
        ("-somepackage", False, "имя пакета должно начинаться с буквы или цифры"),
        ("somepackage=", False, "Недопустимый символ в имени пакета '='"),
        ("пакет", False, "Недопустимый символ в имени пакета 'п'"),
    ],
    ids=[
        "valid-simple",
        "valid-one-char",
        "valid-with-dash",
        "valid-with-underscore",
        "valid-with-dot",
        "valid-with-dash-and-num",
        "valid-max-length",
        "invalid-empty",
        "invalid-too-long",
        "invalid-with-space",
        "invalid-starts-with",
        "invalid-ends-with",
        "invalid-cyrillic",
    ],
)
async def test_is_valid_package_name(name, expected_is_valid, expected_error_part):
    """
    Проверяет валидацию имени пакета по стандарту PEP 508.
    """
    is_valid, err_msg = is_valid_package_name(name=name)

    assert is_valid == expected_is_valid

    if not is_valid:
        assert err_msg == expected_error_part


@pytest.mark.parametrize(
    "name, normalized_name",
    [
        ("Zope.interface", "zope-interface"),
        ("Genshi_Fork", "genshi-fork"),
        ("Flask-GraphQL", "flask-graphql"),
        ("my--package", "my-package"),
        ("some__package", "some-package"),
        ("super...awesome", "super-awesome"),
        ("A.b--C_d", "a-b-c-d"),
        ("already-normalized", "already-normalized"),
    ],
    ids=[
        "replace-dot",
        "replace-underscore",
        "lowercase-only",
        "collapse-double-dash",
        "collapse-double-underscore",
        "collapse-triple-dot",
        "complex-mix",
        "no-changes-needed",
    ],
)
async def test_normalize_package_name(name, normalized_name):
    """
    Проверяет нормализацию имени пакета по PEP 503.
    """
    result = normalize_package_name(name=name)

    assert result == normalized_name
