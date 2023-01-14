from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters
import os
import string
import random
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db

load_dotenv()
API_KEY = os.environ["API_KEY"]

# Setup Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv('DATABASE_URL')
    })

#================================================== UTILITIES ==============================================#
def generate_pass():
    # Takes random choices from ascii_letters and digits
    return ''.join([random.choice(string.ascii_uppercase
                                + string.ascii_lowercase
                                + string.digits)
                                for _ in range(10)])

#=============================================== GENERIC COMMANDS ===========================================#
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ownerId = update.effective_user.id
    otp = generate_pass()
    groupId = update.message.chat.id
    groups = db.reference('/Groups')
    users = db.reference('/Users')

    if ownerId == groupId:
        await context.bot.send_message(chat_id=ownerId, text="You must start the bot from a group!")
        return
    groupEntry = {
        f"{groupId}": {
            "otp": otp,
            "owner": ownerId,
            "facilitators": { },
            "caches": { },
            "players": { }
        }
    }
    
    userEntry = {
        f"{ownerId}": {
            "group_id": groupId,
            "uncompleted_caches": { }
        }
    }

    # cacheEntry = {
    #     f"{cacheId}": {
    #         "name": name,
    #         "lat" : latitude,
    #         "lon": longitude,
    #         "description": description
    #     }
    # }
    
    groups.update(groupEntry)
    users.update(userEntry)
    await context.bot.send_message(chat_id=ownerId, text=otp)

#================================================ OWNER COMMANDS ============================================#

async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    userId = update.effective_user.id
    groupId = update.message.chat.id
    group = db.reference(f"/Groups/{groupId}")
    otp = group.get()["otp"]
    await context.bot.send_message(chat_id=userId, text=f"Your otp is {otp}")

#============================================= FACILITATOR COMMANDS =========================================#

# Allows normal users to become faciliators by entering an otp
GET_OTP = range(1)
async def facil(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userId = update.effective_user.id
    groupId = update.message.chat.id

    if userId == groupId:
        await context.bot.send_message(chat_id=userId, text="You must use this command from a group!")
        return
    context.user_data["group_id"] = groupId
    await context.bot.send_message(chat_id=userId, text="Please enter the OTP", reply_markup=ForceReply(selective=True))
    return GET_OTP
    
async def getOTP(update: Update, context: ContextTypes.DEFAULT_TYPE):
    groupId = context.user_data["group_id"]
    userId = update.effective_user.id
    facil_otp = update.message.text
    group = db.reference(f"/Groups/{groupId}")
    true_otp = group.get()["otp"]
    facilitators = db.reference(f"/Groups/{groupId}/facilitators")
    users = db.reference("/Users")

    if true_otp != facil_otp:
        await update.effective_message.reply_text("Invalid OTP!")
    else:
        # Promote player to facil
        userEntry = {
            userId: {
                "group_id": groupId
            }
        }

        entry = { userId: userId }
        # facilitators.push().set(entry)
        facilitators.update(entry)
        users.update(userEntry)
        await update.effective_message.reply_text("You have been promoted to a facilitator!")
        return ConversationHandler.END

#=============================== FUNCTIONS TO CREATE GEOCACHE =============================#
CACHE_NAME, CACHE_LOCATION, CACHE_DESCRIPTION, CACHE_PROMPT_DELETE = range(4)

# Creates a geocache and adds it to the list of playable caches
async def create_cache(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("You are creating a geocache. To cancel, type /cancel during the process. Please key in the name of this geocache.", reply_markup = ForceReply(selective=True))
    return CACHE_NAME

# Step functions
async def get_cache_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("cache_name")
    name = update.message.text
    print(name)
    context.user_data["name"] = name
    await update.message.reply_text("Please mark the location of this geocache.", reply_markup=ForceReply(selective=True))
    return CACHE_LOCATION

async def get_cache_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    location = update.message.location
    context.user_data["lat"] = location.latitude
    context.user_data["lon"] = location.longitude
    await update.message.reply_text("Please key in the description of this geocache.", reply_markup=ForceReply(selective=True))
    return CACHE_DESCRIPTION

async def get_cache_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = update.message.text
    groupId = update.message.chat_id
    latitude = context.user_data["lat"]
    longitude = context.user_data["lon"]

    # Create the cache in the database
    caches = db.reference("/Caches/")
    # caches = db.reference(f"/Caches/{groupId}")
    all_caches = caches.get()
    if not all_caches:
        cacheId = 69
    else:
        print("all:", all_caches)
        cache_ids = [int(cache) for cache in all_caches]
        print(cache_ids)
        max_cache_id = max(cache_ids) if cache_ids else 0
        print(max_cache_id)
        cacheId = max_cache_id + 1

    cacheEntry = {
        groupId: {
            cacheId: {
                "name": context.user_data["name"],
                "lat" : latitude,
                "lon": longitude,
                "description": description            
            }
        }
    }
    
    caches.set(cacheEntry)
    print(cacheId)

    return ConversationHandler.END

# async def prompt_cancel_create_cache(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     keyboard = [
#         [
#             InlineKeyboardButton("Yes"),
#             InlineKeyboardButton("No")
#         ]
#     ]
#     reply_keyboard = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text("You have entered an invalid input. Would you like to cancel the creation of the geocache?", reply_markup=reply_keyboard)

async def cancel_create_cache(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Cancelled the creation of the cache.")
    return ConversationHandler.END

# ========================================================================================#

# Pulls up a list of the current geocaches and allows you to delete by pressing a button
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caches = db.reference("/Caches")
    all_caches = caches.get()
    if not all_caches:
        await update.effective_message.reply_text("There are no geocaches in the database.")
    else:
        keyboard = []
        for cache in all_caches:
            cacheId = cache["cacheId"]
            cacheName = cache["name"]
            keyboard.append(InlineKeyboardButton(cache.get()["cache_name"], callback_data=cacheId))
            delete_keyboard = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("Please choose the geocache you wish to delete.\n", reply_markup=delete_keyboard)
        

# Resets all the data and deletes all saved geocaches
async def reset_all_forever_serious(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

# Checks if the geocache list has at least 1 valid geocache and starts the game
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    groupId = update.message.chat.id
    players = db.reference(f"/Group/{groupId}/players")
    caches = db.reference(f"/Caches/{groupId}").get()

    all_caches = dict()
    for cache in caches:
        all_caches[cache] = cache
    for player in players.get():
        playerEntry = {
            "uncompleted_caches": all_caches
        }
        db.reference(f"/Group/{groupId}/players/{player}").update(playerEntry)
    await update.effective_message.reply_text("Game has started!")

# Ends the current game if the game is active
async def endplay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

#========================================= PLAYER COMMANDS =========================================#

# If there is an active game, join the game
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    userId = update.effective_user.id
    groupId = update.message.chat.id
    players = db.reference(f'/Groups/{groupId}/players')
    users = db.reference('/Users')

    if userId == groupId:
        await context.bot.send_message(chat_id=userId, text="You must enter this command from a group!")
        return
    
    playerEntry = {
        userId: userId
    }

    userEntry = {
        userId: {
            "group_id": groupId
        }
    }

    players.update(playerEntry)
    users.update(userEntry)

    await context.bot.send_message(chat_id=userId, text="You have joined the game!")

# Submit when a geocache is found
async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

# Gets a list of undiscovered geocaches
async def list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    userId = update.effective_user.id
    user = db.reference(f'/Users/{userId}')
    groupId = user.get()["group_id"]
    player = db.reference(f'/Groups/{groupId}/players/{userId}')
    uncompleted_caches = player.get()["uncompleted_caches"]
    
    keyboard = []
    for cacheId in uncompleted_caches:
      cache = db.reference(f"/Caches/{cacheId}")
      keyboard.append(InlineKeyboardButton(cache.get()["cache_name"], callback_data=cacheId))
    markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Here's the list of caches you have not found yet:\n", reply_markup=markup) 
 
# Views a specific geocache's location, name and description
async def view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chatId = update.message.chat.id
    cacheId = update.callback_query.data
    cache = db.reference(f"/Caches/{cacheId}")
    await update.bot.send_location(chatId, latitude=cache.get()["lat"], longitude=cache.get()["lon"], horizontal_accuracy=300, protect_content=True)
    
    msg = f"Geocache Name:\n{cache.get()['cacheName']}\n\nDescription:\n{cache.get()['cacheDescription']}"
    await update.message.reply_text(msg)

if __name__ == '__main__':
    app = ApplicationBuilder().token(API_KEY).build()
    # Application.concurrent_updates = False

    create_cache_conversation_handler = ConversationHandler(
        entry_points = [CommandHandler('create_cache', create_cache)],
        states = {
            CACHE_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), get_cache_name)],
            CACHE_LOCATION: [MessageHandler(filters.LOCATION & (~filters.COMMAND), get_cache_location)],
            CACHE_DESCRIPTION: [MessageHandler(filters.TEXT & (~filters.COMMAND), get_cache_description)]
        },
        fallbacks = [CommandHandler('cancel', cancel_create_cache)]
    )

    create_facil_conversation_handler = ConversationHandler(
        entry_points = [CommandHandler('facil', facil)],
        states = {
            GET_OTP: [MessageHandler(filters.TEXT, getOTP)],
        },
        fallbacks=[],
        per_chat=False,
    )

    # COPY AND PASTE BELOW FOR NEW COMMANDS
    # app.add_handler(CommandHandler('SLASH_TEXT', FN_NAME))
    app.add_handler(CommandHandler('start', start))

    # Owner functions
    app.add_handler(CommandHandler('get_otp', get_otp))

    # Facilitator functions
    # app.add_handler(CommandHandler('facil', facil))
    app.add_handler(CommandHandler('delete', delete))
    app.add_handler(CommandHandler('reset_all_forever_serious', reset_all_forever_serious))
    app.add_handler(CommandHandler('play', play))
    app.add_handler(CommandHandler('endplay', endplay))
    
    # Player functions
    app.add_handler(CommandHandler('join', join))
    app.add_handler(CommandHandler('submit', submit))
    app.add_handler(CommandHandler('list', list))
    app.add_handler(CommandHandler('view', view))

    # Create cache handlers
    app.add_handler(create_facil_conversation_handler)
    app.add_handler(create_cache_conversation_handler)

    app.run_polling()
