from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Callable, Self, override

from discord import (
    ButtonStyle,
    Color,
    Embed,
    Emoji,
    Interaction,
    PartialEmoji,
    SelectOption,
    ui,
)
from typing_extensions import TypeIs


class OptionItemMixin[ViewT: OptionsView, ValueT](ABC):
    _fget: Callable[[ViewT], ValueT]
    _fset: Callable[[ViewT, str], None] | None

    @property
    @abstractmethod
    def view(self) -> ViewT | None: ...

    @abstractmethod
    def refresh(self): ...

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
            await self.view.on_option_item_error(interaction, e)
        else:
            if changed := (old_value != self.value):
                self.refresh()
            await self.view.on_option_item_success(interaction, changed)

    def setter(self, fset: Callable[[ViewT, str], None]):
        self._fset = fset
        return fset


class OptionButtonModal(ui.Modal):
    value_input = ui.TextInput[Any]()
    value_label = ui.Label[Any](text="Value", component=value_input)

    def __init__(self, button: OptionButton[Any, Any]):
        super().__init__(title=button.name)
        self.button = button
        if button.value is not None:
            self.value_input.default = str(button.value)
        self.value_input.required = button.required

    async def on_submit(self, interaction: Interaction):
        await self.button.set_value(interaction, self.value_input.value)


class OptionButton[ViewT: OptionsView, ValueT](
    ui.Button[ViewT],
    OptionItemMixin[ViewT, ValueT],
):
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
        self._fget = fget
        self._fset = fset

    @override
    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(OptionButtonModal(self))

    @override
    def refresh(self):
        self.label = f"{self.name} ({self.value})"


def option_button(
    *,
    name: str,
    required: bool,
    style: ButtonStyle = ButtonStyle.secondary,
    emoji: str | Emoji | PartialEmoji | None = None,
    row: int | None = None,
):
    def decorator[ViewT: OptionsView, ValueT](fget: Callable[[ViewT], ValueT]):
        return OptionButton(
            name=name,
            required=required,
            fget=fget,
            style=style,
            emoji=emoji,
            row=row,
        )

    return decorator


class OptionSelect[ViewT: OptionsView](ui.Select[ViewT], OptionItemMixin[ViewT, str]):
    def __init__(
        self,
        *,
        labels: list[str],
        fget: Callable[[ViewT], str],
        fset: Callable[[ViewT, str], None] | None = None,
        row: int | None = None,
    ):
        super().__init__(
            options=[
                SelectOption(label=label, value=str(i))
                for i, label in enumerate(labels)
            ],
            row=row,
        )
        self._fget = fget
        self._fset = fset

    @override
    async def callback(self, interaction: Interaction):
        assert len(self.values) == 1, "Invalid state, expected 1 selected value"
        i = int(self.values[0])
        await self.set_value(interaction, self.options[i].label)

    @override
    def refresh(self):
        for option in self.options:
            option.default = self.value == option.label


def option_select(
    *,
    labels: list[str],
    row: int | None = None,
):
    def decorator[ViewT: OptionsView](fget: Callable[[ViewT], str]):
        return OptionSelect(
            labels=labels,
            fget=fget,
            row=row,
        )

    return decorator


type OptionItem[T: OptionsView] = OptionButton[T, Any] | OptionSelect[T]


def is_option_item[T: OptionsView](item: ui.Item[T]) -> TypeIs[OptionItem[T]]:
    return isinstance(item, (OptionButton, OptionSelect))


class OptionsView(ui.View, ABC):
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.__option_items__ = dict[str, OptionItem[Self]]()
        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if is_option_item(member):
                    cls.__option_items__[name] = member

    def __init__(self, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)

        for name, item in self.__option_items__.items():
            item = copy.deepcopy(item)
            setattr(self, name, item)
            self.add_item(item)
            item.refresh()

    @abstractmethod
    async def on_change(self, interaction: Interaction): ...

    def refresh_option_items(self):
        for item in self.children:
            if is_option_item(item):
                item.refresh()

    async def on_option_item_success(
        self,
        interaction: Interaction,
        changed: bool,
    ):
        if changed:
            await self.on_change(interaction)
        else:
            await interaction.response.defer()

    async def on_option_item_error(
        self,
        interaction: Interaction,
        error: ValueError,
    ):
        await interaction.response.send_message(
            embed=Embed(
                title="Invalid input!",
                description=f"```\n{error}\n```",
                color=Color.red(),
                timestamp=datetime.now(UTC),
            ).set_footer(
                text=error.__class__.__name__,
            ),
            ephemeral=True,
        )
