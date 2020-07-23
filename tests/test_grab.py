import pytest
import asyncio
from witnessme.commands import Grab


@pytest.mark.asyncio
async def test_grab_xpath(capsys):
    g = Grab(target=["https://www.google.com"], xpath="//div")
    await g.start()

    captured = capsys.readouterr()
    assert len(captured.out) > 0


@pytest.mark.asyncio
async def test_grab_links(capsys):
    g = Grab(target=["https://www.google.com"], links=True)
    await g.start()

    captured = capsys.readouterr()
    assert len(captured.out) > 0
    assert (
        len(
            list(
                filter(
                    lambda m: m.lower().startswith("https://mail.google.com/"),
                    captured.out.splitlines(),
                )
            )
        )
        == 1
    )
