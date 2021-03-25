import os

import dotenv
from quart import Quart, render_template, redirect, url_for
from quart_discord import DiscordOAuth2Session, Unauthorized, AccessDenied
from quart_discord.utils import requires_authorization

import config
from . import app_config

dotenv.load_dotenv()

app = Quart(__name__)

app.secret_key = os.getenv("QUART_KEY")
app.config["DISCORD_CLIENT_ID"] = config.BOT_ID
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = config.REDIRECT_URI
app.config["DISCORD_BOT_TOKEN"] = os.getenv("TOKEN")

discord = DiscordOAuth2Session(app)


# Jump Routes
@app.route("/support/")
async def support():
    return redirect(config.SUPPORT_INVITE)


@app.route("/invite/")
async def invite():
    return redirect(config.BOT_INVITE)


@app.route("/slash-auth/")
async def slash_auth():
    return redirect(config.SLASH_AUTH)


@app.route("/docs/")
async def docs():
    return redirect(config.DOCS)


# Dashboard Routes
@app.route("/dashboard/servers/")
@requires_authorization
async def servers():
    user = await discord.fetch_user()
    guilds = await discord.fetch_guilds()
    return await render_template(
        "dashboard/server_picker.jinja", user=user, guilds=guilds
    )


@app.route("/dashboard/profile/")
@requires_authorization
async def profile():
    user = await discord.fetch_user()
    return await render_template("dashboard/account_settings.jinja", user=user)


@app.route("/dashboard/premium/")
@requires_authorization
async def profile_premium():
    user = await discord.fetch_user()
    return await render_template("dashboard/premium.jinja", user=user)


# Base Routes
@app.route("/")
async def index():
    try:
        user = await discord.fetch_user()
    except Unauthorized:
        user = None
    return await render_template(
        "home.jinja", user=user, sections=app_config.SECTIONS
    )


@app.route("/premium/")
async def premium():
    try:
        user = await discord.fetch_user()
    except Unauthorized:
        user = None
    return await render_template("premium.jinja", user=user)


@app.route("/leaderboard/")
async def leaderboard():
    try:
        user = await discord.fetch_user()
    except Unauthorized:
        user = None
    return await render_template("leaderboard.jinja", user=user)


@app.route("/login/")
async def login():
    return await discord.create_session()


@app.route("/logout/")
async def logout():
    discord.revoke()
    return redirect(url_for("index"))


@app.route("/api/callback/")
async def login_callback():
    await discord.callback()
    return redirect(url_for("servers"))


@app.errorhandler(Unauthorized)
async def handle_unauthorized(e):
    return redirect(url_for("login"))


@app.errorhandler(AccessDenied)
async def handle_access_denied(e):
    return redirect(url_for("index"))
