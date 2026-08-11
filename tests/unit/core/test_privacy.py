import pytest

from app.core.privacy import UNKNOWN_EXT, UNKNOWN_REF, USER_REF_LENGTH, file_ext, user_ref


def test_user_ref_is_stable() -> None:
    assert user_ref(12345) == user_ref(12345)


def test_user_ref_differs_between_users() -> None:
    assert user_ref(12345) != user_ref(12346)


def test_user_ref_hides_original_id() -> None:
    ref = user_ref(12345)
    assert "12345" not in ref
    assert len(ref) == USER_REF_LENGTH


def test_user_ref_without_id() -> None:
    assert user_ref(None) == UNKNOWN_REF


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("Иванов_Иван_резюме.pdf", "pdf"),
        ("resume.PDF", "pdf"),
        ("archive.tar.gz", "gz"),
        ("noextension", UNKNOWN_EXT),
        ("", UNKNOWN_EXT),
        (None, UNKNOWN_EXT),
        ("resume.exe.вирус", UNKNOWN_EXT),
        ("resume." + "a" * 20, UNKNOWN_EXT),
    ],
)
def test_file_ext_keeps_only_extension(file_name: str | None, expected: str) -> None:
    assert file_ext(file_name) == expected
