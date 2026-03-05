import os
import logging
from flask import Flask
from threading import Thread
from datetime import datetime
import pytz

import nextcord
from nextcord.ext import commands, tasks
from nextcord import ui
from nextcord.interactions import Interaction

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nextcord')
logger.setLevel(logging.INFO)

# Flask app for UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 2 is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8081)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Bot setup
intents = nextcord.Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(intents=intents, help_command=None)

# Channel IDs
PROMO_CHANNEL_ID = 1471649067951198238
INFRACT_CHANNEL_ID = 1471649138054795398

# Role IDs - Staff Hierarchy
ROLE_IDS = {
    # Ownership
    "owner": 1471642523821674618,
    "co_owner": 1471642550271082690,
    "holding": 1471642360503992411,
    
    # Executive
    "name_executive": 1471642668630020268,
    "partner_executive": 1471642626863141059,
    "associate_executive": 1471642323657031754,
    "executive": 1471642126663024640,
    
    # Management
    "top_manager": 1471687503135248625,
    "senior_manager": 1471646332799418601,
    "junior_manager": 1471640133462659236,
    "intern_manager": 1471646520909758666,
    "management": 1471641915215843559,
    
    # Supervision
    "top_supervisor": 1471646257679171687,
    "senior_supervisor": 1471646221604098233,
    "junior_supervisor": 1471646134098460743,
    "intern_supervisor": 1471640008011026666,
    "supervision": 1471641790112333867,
    
    # Evaluation
    "top_evaluator": 1472073458321063987,
    "senior_evaluator": 1472073396451020953,
    "junior_evaluator": 1472073148949336215,
    "intern_evaluator": 1472073043554734100,
    "evaluation": 1472072792081170682,
    
    # Administration
    "lead_administrator": 1471645738734714982,
    "senior_administrator": 1471645702357520468,
    "junior_administrator": 1471646093287755796,
    "trial_administrator": 1471647027896254557,
    "administration": 1471640542231396373,
    
    # Moderation
    "lead_moderator": 1471642772359479420,
    "senior_moderator": 1471642726796628048,
    "junior_moderator": 1471646011741966517,
    "trial_moderator": 1471646061369098375,
    "moderation": 1471640225015922982,
}

# Staff roles list for dropdown
STAFF_ROLES = [
    ("Trial Moderator", ROLE_IDS["trial_moderator"], "moderation"),
    ("Junior Moderator", ROLE_IDS["junior_moderator"], "moderation"),
    ("Senior Moderator", ROLE_IDS["senior_moderator"], "moderation"),
    ("Lead Moderator", ROLE_IDS["lead_moderator"], "moderation"),
    ("Trial Administrator", ROLE_IDS["trial_administrator"], "administration"),
    ("Junior Administrator", ROLE_IDS["junior_administrator"], "administration"),
    ("Senior Administrator", ROLE_IDS["senior_administrator"], "administration"),
    ("Lead Administrator", ROLE_IDS["lead_administrator"], "administration"),
    ("Intern Evaluator", ROLE_IDS["intern_evaluator"], "evaluation"),
    ("Junior Evaluator", ROLE_IDS["junior_evaluator"], "evaluation"),
    ("Senior Evaluator", ROLE_IDS["senior_evaluator"], "evaluation"),
    ("Top Evaluator", ROLE_IDS["top_evaluator"], "evaluation"),
    ("Intern Supervisor", ROLE_IDS["intern_supervisor"], "supervision"),
    ("Junior Supervisor", ROLE_IDS["junior_supervisor"], "supervision"),
    ("Senior Supervisor", ROLE_IDS["senior_supervisor"], "supervision"),
    ("Top Supervisor", ROLE_IDS["top_supervisor"], "supervision"),
    ("Intern Manager", ROLE_IDS["intern_manager"], "management"),
    ("Junior Manager", ROLE_IDS["junior_manager"], "management"),
    ("Senior Manager", ROLE_IDS["senior_manager"], "management"),
    ("Top Manager", ROLE_IDS["top_manager"], "management"),
    ("Executive", ROLE_IDS["executive"], "executive"),
    ("Associate Executive", ROLE_IDS["associate_executive"], "executive"),
    ("Partner Executive", ROLE_IDS["partner_executive"], "executive"),
    ("Name Executive", ROLE_IDS["name_executive"], "executive"),
]

# Staff emojis
STAFF_EMOJIS = {
    "moderation": "<:ModerationTeam:1477360980995342366>",
    "administration": "<:AdministrationTeam:1477360939664674957>",
    "evaluation": "<:EvaluationTeam:1477360862594596914>",
    "supervision": "<:SupervisionTeam:1477360821779566702>",
    "management": "<:ManagementTeam:1477360784710566092>",
    "executive": "<:BoardofExecutives:1477360743132430591>",
    "holding": "<:HoldingGroup:1477360688333721600>",
}

# Cooldowns (in days)
PROMOTION_COOLDOWNS = {
    "moderation": 3,
    "administration": 4,
    "evaluation": 5,
    "supervision": 7,
    "management": 14,
    "executive": 30,
}

# Minimum role required to promote
MIN_PROMOTE_ROLE = ROLE_IDS["intern_supervisor"]

# Senior Manager+ for cooldown skip
SENIOR_MANAGER_ROLE = ROLE_IDS["senior_manager"]


def get_staff_team(role_id: int) -> str:
    """Get the team name for a role."""
    for name, rid, team in STAFF_ROLES:
        if rid == role_id:
            return team
    return "unknown"


def get_cooldown_days(role_id: int) -> int:
    """Get cooldown days for a role's team."""
    team = get_staff_team(role_id)
    return PROMOTION_COOLDOWNS.get(team, 30)


def get_role_by_name(name: str):
    """Get role ID by name."""
    for role_name, role_id, team in STAFF_ROLES:
        if role_name.lower() == name.lower():
            return role_id, team
    return None, None


def check_can_promote(user) -> bool:
    """Check if user can promote (has Intern Supervisor+ role)."""
    for role in user.roles:
        if role.id >= MIN_PROMOTE_ROLE:
            return True
    return False


def check_senior_manager(user) -> bool:
    """Check if user is Senior Manager or higher."""
    for role in user.roles:
        if role.id >= SENIOR_MANAGER_ROLE:
            return True
    return False


@bot.event
async def on_ready():
    """Bot is ready and logged in."""
    logger.info(f'Bot 2 logged in as {bot.user}')


# ===== SLASH COMMANDS =====

@bot.slash_command(name="promote", description="Promote a staff member")
async def promote(interaction: Interaction, member: nextcord.Member = None):
    """Staff promotion command."""
    await interaction.response.defer(ephemeral=True)
    
    # Check if user can promote
    if not check_can_promote(interaction.user):
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Permission Denied",
            description="You need to be **Intern Supervisor** or higher to promote staff members.",
            color=0xff0000
        )
        await interaction.send(embed=embed, ephemeral=True)
        return
    
    # If member is provided, show rank selection
    if member:
        # Check if member has staff role
        has_staff = False
        member_role_ids = [r.id for r in member.roles]
        for _, role_id, _ in STAFF_ROLES:
            if role_id in member_role_ids:
                has_staff = True
                break
        
        if not has_staff:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Invalid Member",
                description="That member is not a part of the Staff Team. Please ensure you are attempting to promote someone who is staff.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        # Show rank selection view
        view = RankSelectView(member, interaction.user)
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Select Promotion Rank",
            description=f"Select the rank to promote **{member.name}** to:",
            color=0x4bbfff
        )
        await interaction.send(embed=embed, view=view, ephemeral=True)
    else:
        # Show help embed
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Staff Promotion",
            description="To promote a staff member, please mention them:\n\n`/promote @member`\n\nThen you will be prompted to select the new rank.",
            color=0x4bbfff
        )
        await interaction.send(embed=embed, ephemeral=True)


@bot.slash_command(name="infract", description="Infract a staff member")
async def infract(
    interaction: Interaction,
    member: nextcord.Member,
    reason: str,
    severity: str = "Warning"
):
    """Infract a staff member."""
    await interaction.response.defer(ephemeral=True)
    
    # Check if user can promote (same permission)
    if not check_can_promote(interaction.user):
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Permission Denied",
            description="You need to be **Intern Supervisor** or higher to infract staff members.",
            color=0xff0000
        )
        await interaction.send(embed=embed, ephemeral=True)
        return
    
    # Check if member has staff role
    has_staff = False
    member_role_ids = [r.id for r in member.roles]
    for _, role_id, _ in STAFF_ROLES:
        if role_id in member_role_ids:
            has_staff = True
            break
    
    if not has_staff:
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Invalid Member",
            description="That member is not a part of the Staff Team. Please ensure you are attempting to infract someone who is staff.",
            color=0xff0000
        )
        await interaction.send(embed=embed, ephemeral=True)
        return
    
    # Send to infract channel
    infract_channel = bot.get_channel(INFRACT_CHANNEL_ID)
    if infract_channel:
        team = get_staff_team(member_role_ids[0]) if member_role_ids else "unknown"
        emoji = STAFF_EMOJIS.get(team, "<:ILSRP:1471990869166002291>")
        
        embed = nextcord.Embed(
            title=f"{emoji} | ILSRP Staff Infraction",
            color=0xff0000
        )
        embed.add_field(name="Staff Member", value=f"{member.mention}", inline=True)
        embed.add_field(name="Initiated By", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="Infraction Type", value=severity, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await infract_channel.send(embed=embed)
        
        success_embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Infraction Filed",
            description=f"Successfully filed **{severity}** against {member.mention}.",
            color=0x00ff00
        )
        await interaction.send(embed=success_embed, ephemeral=True)
    else:
        await interaction.send("Error: Infract channel not found.", ephemeral=True)


@bot.slash_command(name="promotions", description="Promotion management menu")
async def promotions(interaction: Interaction):
    """Main promotions menu with dropdown embed."""
    embed = nextcord.Embed(
        title="<:ILSRP:1471990869166002291> | ILSRP Promotion System",
        description="Welcome to the Staff Promotion Management System\n\nSelect an option from the dropdown below:",
        color=0x4bbfff
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1472412365415776306/1473135761078358270/welcomeilsrp.png")
    
    view = PromotionMenuView()
    await interaction.send(embed=embed, view=view, ephemeral=True)


# ===== VIEWS =====

class RankSelectView(ui.View):
    def __init__(self, member, promoter):
        super().__init__()
        self.member = member
        self.promoter = promoter
        
        # Create select options for ranks
        options = []
        for name, rid, team in STAFF_ROLES:
            emoji = STAFF_EMOJIS.get(team, "")
            options.append(ui.SelectOption(label=name, value=name, emoji=emoji if emoji else None))
        
        select = ui.Select(
            placeholder="Select a rank",
            options=options
        )
        select.callback = self.rank_selected
        self.add_item(select)
    
    async def rank_selected(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        new_rank = interaction.data["values"][0]
        
        # Show reason modal
        modal = PromotionReasonModal(self.member, self.promoter, new_rank)
        await interaction.send_modal(modal)


class PromotionReasonModal(ui.Modal):
    def __init__(self, member, promoter, new_rank):
        super().__init__("Promotion Reason")
        self.member = member
        self.promoter = promoter
        self.new_rank = new_rank
        
        self.approval_input = ui.TextInput(
            label="(Optional) Did anyone approve of the promotion?",
            placeholder="Leave empty if no approval needed",
            style=nextcord.TextInputStyle.short,
            required=False
        )
        
        self.reason_input = ui.TextInput(
            label="Reason for promotion",
            placeholder="Enter the reason",
            style=nextcord.TextInputStyle.paragraph,
            required=True
        )
        
        self.add_item(self.approval_input)
        self.add_item(self.reason_input)
    
    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        approval = self.approval_input.value if self.approval_input.value else "NOTHING HERE"
        reason = self.reason_input.value
        
        # Get role ID for new rank
        new_role_id, new_team = get_role_by_name(self.new_rank)
        
        if not new_role_id:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Invalid Rank",
                description=f"**{self.new_rank}** is not a valid staff rank.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        # Check cooldown
        promo_channel = bot.get_channel(PROMO_CHANNEL_ID)
        if promo_channel:
            cst = pytz.timezone('America/Chicago')
            now = datetime.now(cst)
            
            async for message in promo_channel.history(limit=50):
                if f"<@{self.member.id}>" in message.content or f"<@!{self.member.id}>" in message.content:
                    if message.created_at:
                        days_since = (now - message.created_at.replace(tzinfo=cst)).days
                        member_role_ids = [r.id for r in self.member.roles]
                        cooldown_days = get_cooldown_days(member_role_ids[0]) if member_role_ids else 30
                        
                        if days_since < cooldown_days:
                            if approval != "NOTHING HERE" and check_senior_manager(interaction.user):
                                pass
                            else:
                                embed = nextcord.Embed(
                                    title="<:ILSRP:1471990869166002291> | Cooldown Active",
                                    description=f"This staff member is on cooldown. They were promoted **{days_since} days ago**.\n\n"
                                               f"Required cooldown: **{cooldown_days} days**\n\n"
                                               f"To skip cooldown, get approval from a **Senior Manager+** and enter their name in the approval field.",
                                    color=0xff0000
                                )
                                await interaction.send(embed=embed, ephemeral=True)
                                return
                    break
        
        # Get current roles
        current_role_ids = [r.id for r in self.member.roles]
        old_role_id = None
        old_team = None
        for _, role_id, team in STAFF_ROLES:
            if role_id in current_role_ids:
                old_role_id = role_id
                old_team = team
                break
        
        # Update roles
        try:
            # Remove old role
            if old_role_id:
                old_role = interaction.guild.get_role(old_role_id)
                if old_role:
                    await self.member.remove_roles(old_role)
            
            # Add new role
            new_role = interaction.guild.get_role(new_role_id)
            if new_role:
                await self.member.add_roles(new_role)
            
            # Get old rank name
            old_rank_name = "N/A"
            for name, rid, _ in STAFF_ROLES:
                if rid == old_role_id:
                    old_rank_name = name
                    break
            
            # Send promotion message
            old_emoji = STAFF_EMOJIS.get(old_team, "<:ILSRP:1471990869166002291>")
            new_emoji = STAFF_EMOJIS.get(new_team, "<:ILSRP:1471990869166002291>")
            
            promo_embed = nextcord.Embed(
                title="# <:ILSRP:1471990869166002291> | ILSRP Staff Promotion",
                color=0x4bbfff
            )
            promo_embed.add_field(name="`Staff Member:`", value=f"{self.member.mention}", inline=False)
            promo_embed.add_field(name="`Initiated By:`", value=f"{self.promoter.mention}", inline=False)
            promo_embed.add_field(name="`Approved By:`", value=approval, inline=False)
            promo_embed.add_field(name="`Former Position:`", value=f"{old_rank_name} {old_emoji}", inline=False)
            promo_embed.add_field(name="`Updated Position:`", value=f"{self.new_rank} {new_emoji}", inline=False)
            promo_embed.add_field(name="`Reason:`", value=reason, inline=False)
            
            if promo_channel:
                await promo_channel.send(embed=promo_embed)
            
            success_embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Promotion Successful",
                description=f"Successfully promoted **{self.member.name}** to **{self.new_rank}**!",
                color=0x00ff00
            )
            await interaction.send(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Error",
                description=f"Failed to update roles: {str(e)}",
                color=0xff0000
            )
            await interaction.send(embed=error_embed, ephemeral=True)


class PromotionMenuView(ui.View):
    def __init__(self):
        super().__init__()
        
        select = ui.Select(
            placeholder="Select an option",
            options=[
                ui.SelectOption(label="Staff Promote", description="Promote a staff member", emoji="📈"),
                ui.SelectOption(label="Cooldown Information", description="View promotion cooldowns", emoji="⏰"),
                ui.SelectOption(label="Manage Promotions", description="Manage staff promotions", emoji="⚙️")
            ]
        )
        select.callback = self.menu_callback
        self.add_item(select)
    
    async def menu_callback(self, interaction: Interaction):
        value = interaction.data["values"][0]
        
        if value == "Staff Promote":
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Staff Promote",
                description="To promote a staff member, use:\n\n`/promote @member`\n\nThen you will be asked to select the new rank and provide a reason.",
                color=0x4bbfff
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        elif value == "Cooldown Information":
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Cooldown Information",
                description="Promotion cooldowns by team:\n\n"
                           f"{STAFF_EMOJIS['moderation']} **Moderation:** 3 days\n"
                           f"{STAFF_EMOJIS['administration']} **Administration:** 4 days\n"
                           f"{STAFF_EMOJIS['evaluation']} **Evaluation:** 5 days\n"
                           f"{STAFF_EMOJIS['supervision']} **Supervision:** 7 days\n"
                           f"{STAFF_EMOJIS['management']} **Management:** 14 days (2 weeks)\n"
                           f"{STAFF_EMOJIS['executive']} **Executive:** 30 days (1 month)\n\n"
                           "*Cooldown skipping requires Senior Manager+ approval*",
                color=0x4bbfff
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        elif value == "Manage Promotions":
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Manage Promotions",
                description="This feature is under development.\n\nContact a developer for additional management options.",
                color=0x4bbfff
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


# ===== RUN BOT =====

if __name__ == "__main__":
    TOKEN = os.environ.get("TOKEN")
    if not TOKEN:
        logger.error("TOKEN environment variable not set!")
        print("ERROR: Please set the TOKEN environment variable!")
        exit(1)
    
    # Start Flask server for UptimeRobot
    keep_alive()
    
    # Run the bot
    bot.run(TOKEN)

