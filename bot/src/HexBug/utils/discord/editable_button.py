from __future__ import annotations

import asyncio
import copy
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable, Self

from discord import (
    AllowedMentions,
    ButtonStyle,
    Color,
    Embed,
    Emoji,
    Interaction,
    PartialEmoji,
    ui,
)


class EditableButtonModal(ui.Modal):
    value_input = ui.TextInput[Self](label="Value")

    def __init__(self, button: EditableButton[Any, Any]):
        super().__init__(title=button.name)
        self.button = button
        if button.value is not None:
            self.value_input.default = str(button.value)
        self.value_input.required = button.required

    async def on_submit(self, interaction: Interaction):
        await self.button.set_value(interaction, self.value_input.value)


class EditableButton[ViewT: EditableButtonView, ValueT](ui.Button[ViewT]):
    def __init__(
        self,
        *,
        name: str,
        required: bool,
        fget: Callable[[ViewT], ValueT],
        fset: Callable[[ViewT, str], None] | None = None,
        style: ButtonStyle = ButtonStyle.secondary,
        emoji: str | Emoji | PartialEmoji | None = None,
        row: int | None = None,
    ):
        super().__init__(
            style=style,
            emoji=emoji,
            row=row,
        )
        self.name: str = name
        self.required: bool = required
        self._fget: Callable[[ViewT], ValueT] = fget
        self._fset: Callable[[ViewT, str], None] | None = fset

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(EditableButtonModal(self))

    def refresh_label(self):
        self.label = f"{self.name} ({self.value})"

    @property
    def value(self) -> ValueT:
        if not self.view:
            raise AttributeError
        return self._fget(self.view)

    async def set_value(self, interaction: Interaction, value: str):
        if not (self.view and self._fset):
            raise AttributeError
        old_value = self.value
        try:
            self._fset(self.view, value)
        except ValueError as e:
            await self.view.on_editable_button_error(interaction, e)
        else:
            if changed := (old_value != self.value):
                self.refresh_label()
            await self.view.on_editable_button_success(interaction, changed)

    def setter(self, fset: Callable[[ViewT, str], None]):
        self._fset = fset
        return fset


def editable_button(
    *,
    name: str,
    required: bool,
    style: ButtonStyle = ButtonStyle.secondary,
    emoji: str | Emoji | PartialEmoji | None = None,
    row: int | None = None,
):
    def decorator[ViewT: EditableButtonView, ValueT](fget: Callable[[ViewT], ValueT]):
        return EditableButton(
            name=name,
            required=required,
            fget=fget,
            style=style,
            emoji=emoji,
            row=row,
        )

    return decorator


# TODO: fix the component order being wonky
class EditableButtonView(ui.View):
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.__editable_buttons__ = dict[str, EditableButton[Self, Any]]()
        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if isinstance(member, EditableButton):
                    cls.__editable_buttons__[name] = member

    def _init_editable_buttons(self):
        for name, item in self.__editable_buttons__.items():
            item = copy.deepcopy(item)
            setattr(self, name, item)
            self.add_item(item)
            item.refresh_label()

    def __init__(
        self,
        *,
        on_change: Callable[[], Awaitable[Any]],
        timeout: float | None = 180,
    ):
        super().__init__(timeout=timeout)
        self.on_change = on_change
        self._init_editable_buttons()

    async def on_editable_button_success(
        self,
        interaction: Interaction,
        changed: bool,
    ):
        await asyncio.gather(
            interaction.response.edit_message(
                embed=None,
                view=self,
            ),
            self.on_change() if changed else asyncio.sleep(0),
        )

    async def on_editable_button_error(
        self,
        interaction: Interaction,
        error: ValueError,
    ):
        await interaction.response.edit_message(
            embed=Embed(
                title="Invalid input!",
                description=f"```\n{error}\n```",
                color=Color.red(),
                timestamp=datetime.now(UTC),
            ).set_footer(
                text=error.__class__.__name__,
            ),
            view=self,
            allowed_mentions=AllowedMentions.none(),
        )
