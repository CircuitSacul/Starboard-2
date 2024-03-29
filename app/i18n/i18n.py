import contextvars
import gettext
import os.path
import typing
from glob import glob

import discord

import config
from app.classes.t_string import TString

if typing.TYPE_CHECKING:
    from app.classes.bot import Bot

BASE_DIR = "app/"
LOCALE_DEFAULT = "en_US"
LOCALE_DIR = "locale"
locales = frozenset(
    map(
        os.path.basename,
        filter(os.path.isdir, glob(os.path.join(BASE_DIR, LOCALE_DIR, "*"))),
    )
)

gettext_translations = {
    locale: gettext.translation(
        "bot",
        languages=(locale,),
        localedir=os.path.join(BASE_DIR, LOCALE_DIR),
    )
    for locale in locales
}

gettext_translations["en_US"] = gettext.NullTranslations()
locales |= {"en_US"}


def use_current_gettext(*args, **kwargs) -> str:
    """Translate a string using the proper gettext based
    on the current_locale context var.

    :return: The translated string
    :rtype: str
    """
    if not gettext_translations:
        return gettext.gettext(*args, **kwargs)

    locale = current_locale.get()
    if locale == "testing":
        return "<testing worked>"
    return gettext_translations.get(
        locale, gettext_translations[LOCALE_DEFAULT]
    ).gettext(*args, **kwargs)


@typing.overload
def t_(string: str, as_obj: True) -> TString:
    ...


@typing.overload
def t_(string: str) -> str:
    ...


def t_(string, as_obj=False):
    """Translates or lazy-translates a string.

    :param string: The string that needs translation
    :type string: str
    :param as_obj: Whether or not to use lazy translation, defaults to False
    :type as_obj: bool, optional
    :return: The translated string, or the TString object if lazy
    :rtype: Union[str, TString]
    """
    tstring = TString(string, use_current_gettext)
    if as_obj:
        return tstring
    return str(tstring)  # translate immediatly


current_locale: contextvars.ContextVar = contextvars.ContextVar("i18n")


def set_current_locale():
    """Sets the locale to the LOCALE_DEFAULT."""
    current_locale.set(LOCALE_DEFAULT)


def language_embed(bot: "Bot", p: str) -> discord.Embed:
    """Generates an embed with a list of valid languages.

    :param bot: The bot instance
    :type bot: Bot
    :param p: The used prefix
    :type p: str
    :return: The embed with language info
    :rtype: discord.Embed
    """
    return discord.Embed(
        title="Languages",
        color=bot.theme_color,
        description=t_(
            "You can now choose your personal and server language. "
            "Use `{p}guildLang <language>` to set the language for "
            "the server (applies to starboard messages, level up "
            "messages, etc.), or `{p}lang <language>` to set your "
            "personal language.\n\n"
            "Valid Languages:\n{languages}"
        ).format(
            p=p,
            languages=" - "
            + "\n - ".join(
                [
                    lang["name"]
                    + (" (Partial)" if lang.get("partial", False) else "")
                    for lang in config.LANGUAGE_MAP
                ]
            ),
        ),
    )


set_current_locale()
