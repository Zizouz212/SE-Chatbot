from ChatExchange.chatexchange.client import Client
from ChatExchange.chatexchange.events import MessagePosted
from ChatExchange.chatexchange.messages import Message
import getpass
import re
from HTMLParser import HTMLParser
import thread
import time
import random
import requests
import urllib
import logging.handlers
import os
import os.path
import sys
import pickle
from CommandHelp import CommandHelp
from Config import Config
import Commands
import SaveIO
import Points


class Chatbot:
    def __init__(self):
        self.room = None
        self.client = None
        self.privileged_users = []
        self.owners = []
        self.owner_name = ""
        self.chatbot_name = ""
        self.enabled = True
        self.running = True
        self.waiting_time = -1
        self.latest_word_id = -1
        self.current_word_to_reply_to = ""
        self.latest_words = []
        self.in_shadows_den = False
        self.translation_languages = ["auto", "en", "fr", "nl", "de", "he", "ru", "el", "pt", "es", "fi", "af", "sq", "ar", "hy", "az", "eu", "be", "bn", "bs", "bg", "ca", "ceb", "zh-CN", "hr", "cs", "da",
                                      "eo", "et", "tl", "gl", "ka", "gu", "ht", "ha", "hi", "hmn", "hu", "is", "ig", "id", "ga", "it", "ja", "jw", "kn", "km", "ko", "lo", "la", "lv", "lt", "mk", "ms"
                                      "mt", "mi", "mr", "mn", "ne", "no", "fa", "pl", "pa", "ro", "sr", "sk", "sl", "so", "sw", "sv", "ta", "te", "th", "tr", "uk", "ur", "vi", "cy", "yi", "yo", "zu"]
        self.end_lang = None
        self.translation_chain_going_on = False
        self.translation_switch_going_on = False
        self.links = []
        self.link_explanations = []
        self.banned = {}
        self.site = ""
        self.msg_id_no_reply_found = -1
        self.owner_ids = []
        self.privileged_user_ids = []
        self.commands = {
            'translate': self.command_translate,
            'random': Commands.command_random,
            'randomint': Commands.command_randomint,
            'randomchoice': Commands.command_randomchoice,
            'shuffle': Commands.command_shuffle,
            'listcommands': self.command_listcommands,
            'help': self.command_help,
            'xkcdrandomnumber': Commands.command_xkcdrandomnumber,
            'xkcd': Commands.command_xkcd,
            'alive': Commands.command_alive,
            'utc': Commands.command_utc,
			'points': Commands.command_points
        }
        self.owner_commands = {
            'stop': self.command_stop,
            'disable': self.command_disable,
            'enable': self.command_enable,
            'ban': self.command_ban,
            'unban': self.command_unban,
            'translationchain': self.command_translationchain,
            'translationswitch': self.command_translationswitch,
        }
        self.privileged_commands = {
            'delete': self.command_delete
        }

    def main(self, config_data, additional_general_config):
        if "owners" in Config.General:
            self.owners = Config.General["owners"]
        else:
            sys.exit("Error: no owners found. Please update Config.py.")
        if "privileged_users" in config_data:
            self.privileged_users = config_data["privileged_users"]
        if "owner_name" in Config.General:
            self.owner_name = Config.General["owner_name"]
        else:
            sys.exit("Error: no owner name found. Please update Config.py.")
        if "chatbot_name" in Config.General:
            self.chatbot_name = Config.General["chatbot_name"]
        else:
            sys.exit("Error: no chatbot name found. Please update Config.py.")
        # self.setup_logging() # if you want to have logging, un-comment this line
        self.in_shadows_den = False
        if "site" in config_data:
            self.site = config_data["site"]
            print("Site: %s" % self.site)
        else:
            self.site = raw_input("Site: ")
        for o in self.owners:
            if self.site in o:
                self.owner_ids.append(o[self.site])
        if len(self.owner_ids) < 1:
            sys.exit("Error: no owners found for this site: %s." % self.site)
        for p in self.privileged_users:
            if self.site in p:
                self.privileged_user_ids.append(p[self.site])
        if "room" in config_data:
            room_number = config_data["room"]
            print("Room number: %i" % room_number)
        else:
            room_number = int(raw_input("Room number: "))
        if "email" in Config.General:
            email = Config.General["email"]
        elif "email" in additional_general_config:
            email = additional_general_config["email"]
        else:
            email = raw_input("Email address: ")
        if "password" in Config.General: # I would not recommend to store the password in Config.py
            password = Config.General["password"]
        elif "password" in additional_general_config:
            password = additional_general_config["password"]
        else:
            password = getpass.getpass("Password: ")
        
        if os.path.isfile("config.txt"): # config.txt is for values that can change at runtime, Config.py is for static data
            f = open("config.txt", "r")
            self.waiting_time = int(f.read())
            f.close()
        else:
            f = open("config.txt", "w")
            f.write("20")
            f.close()

        if os.path.isfile("bannedUsers.txt"):
            with open("bannedUsers.txt", "r") as f:
                self.banned = pickle.load(f)
        self.client = Client(self.site)
        self.client.login(email, password)
    
        self.room = self.client.get_room(room_number)
        self.room.join()
        bot_message = "Bot started with waiting time set to %i seconds." % self.waiting_time if self.in_shadows_den else "Bot started."
        self.room.send_message(bot_message)
        self.room.watch_socket(self.on_event)
        
        while self.running:
            inputted = raw_input("<< ")
            if inputted.strip() == "":
                continue
            if inputted.startswith("$") and len(inputted) > 2:
                command_in = inputted[2:]
                command_out = self.command(command_in, None, None)
                if command_out != False and command_out is not None:
                    print command_out
                    if inputted[1] == "+":
                        self.room.send_message("%s" % command_out)
            else:
                self.room.send_message(inputted)

    def setup_logging(self): # logging method taken from ChatExchange/examples/chat.py
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.DEBUG)

        # In addition to the basic stderr logging configured globally
        # above, we'll use a log file for chatexchange.client.
        wrapper_logger = logging.getLogger('chatexchange.client')
        wrapper_handler = logging.handlers.TimedRotatingFileHandler(
           filename='client.log',
            when='midnight', delay=True, utc=True, backupCount=7,
        )
        wrapper_handler.setFormatter(logging.Formatter(
            "%(asctime)s: %(levelname)s: %(threadName)s: %(message)s"
        ))
        wrapper_logger.addHandler(wrapper_handler)


    def on_event(self, event, client):
        should_return = False
        if not self.enabled:
            should_return = True
        if isinstance(event, MessagePosted) and (not self.enabled) and event.user.id in self.owner_ids and event.message.content.startswith("&gt;&gt;"):
            should_return = False
        if not self.running:
            should_return = True
        if not isinstance(event, MessagePosted):
            should_return = True
        if isinstance(event, MessagePosted) and self.site in self.banned \
                and event.user.id in self.banned[self.site]:
            should_return = True
        if should_return:
            return
        
        message = event.message
        h = HTMLParser()
        content = h.unescape(message.content_source)

        if event.user.id == self.client.get_me().id:
            return

        content = re.sub(r"^>>\s+", ">>", content)
        if not content.startswith(">>"):
            content = re.sub(r"([:;][-']?[)/(DPdpoO\[\]\\|])", "", content) # strip smilies
            content = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", content)
            content = re.sub(r"\(.+?\)", "", content)
        content = re.sub(r"\s+", " ", content)
        content = content.strip()
        parts = content.split(" ")
        if (not parts[0].startswith(">>")) and (len(parts) != 2 or not parts[0].startswith(":")) and (event.user.id != -2):
            return
        
        if len(parts) == 2 and parts[1] == "!delete!" and parts[0].startswith(":"):
            try:
                if event.user.id in self.privileged_user_ids or event.user.id in self.owner_ids:
                    msg_id_to_delete = int(parts[0][1:])
                    self.client.get_message(msg_id_to_delete).delete()
            except:
                pass
        
        if parts[0].startswith(">>"):
            cmd_args = content[2:]
            if (not cmd_args.startswith("translat")) and event.user.id not in self.owner_ids and re.compile("[^a-zA-Z0-9 _-]").search(cmd_args):
                message.reply("Command contains invalid characters.")
                return
            output = self.command(cmd_args, message, event)
            if output != False and output is not None:
                if len(output) > 500:
                    message.reply("Output would be longer than 500 characters (the limit), so only the first 500 characters are posted now.")
                    self.room.send_message(output[:500])
                else:
                    message.reply(output)


    def command(self, cmd, msg, event):
        cmd_args = cmd.split(' ')
        cmd_name = cmd_args[0].lower()
        args = cmd_args[1:]
        if cmd_name == "translationchain" or cmd_name == "translationswitch":
            to_translate = " ".join(args[3:])
            args = args[:3]
            args.append(to_translate)
        elif cmd_name == "translate":
            to_translate = " ".join(args[2:])
            args = args[:2]
            args.append(to_translate)
        commands_to_use = self.commands.copy()
        if cmd_name in commands_to_use:
            return commands_to_use[cmd_name](args, msg, event)

        elif cmd_name in self.owner_commands:
            if msg is None or event.user.id in self.owner_ids:
                return self.owner_commands[cmd_name](args, msg, event)
            else:
                return "You don't have the privilege to execute this command."
        elif cmd_name in self.privileged_commands:
            if msg is None or event.user.id in self.privileged_user_ids or event.user.id in self.owner_ids:
                return self.privileged_commands[cmd_name](args, msg, event)
            else:
                return "You don't have the privilege to execute this command."
        else:
            return "Command not found."
                
    def command_stop(self, args, msg, event):
        SaveIO.save(SaveIO.path, Points.Points)
        self.enabled = False
        self.running = False
        if msg is not None:
            msg.reply("Bot terminated.")
            time.sleep(2)
        self.room.leave()
        self.client.logout()
        time.sleep(5)
        os._exit(0)
        
    def command_disable(self, args, msg, event):
        self.enabled = False
        return "Bot disabled, run >>enable to enable it again."
        
    def command_enable(self, args, msg, event):
        self.enabled = True
        return "Bot enabled."

    
    def command_ban(self, args, msg, event):
        try:
            banned_user = int(args[0])
        except ValueError:
            return "Invalid arguments."
        try:
            user_name = self.client.get_user(banned_user).name.replace(" ", "")
        except:
            return "Could not fetch user; please check whether the user exists."
        if not self.site in self.banned:
            self.banned[self.site] = []
        if not banned_user in self.banned[self.site]:
            self.banned[self.site].append(banned_user)
        else:
            return "Already banned."
        with open("bannedUsers.txt", "w") as f:
            pickle.dump(self.banned, f)
        return "User @%s has been banned." % user_name
            
    def command_unban(self, args, msg, event):
        try:
            banned_user = int(args[0])
        except ValueError:
            return "Invalid arguments."
        try:
            user_name = self.client.get_user(banned_user).name.replace(" ", "")
        except:
            return "Could not fetch user; please check whether the user exists."
        if not self.site in self.banned:
            return "Not banned."
        if not banned_user in self.banned[self.site]:
            return "Not banned."
        self.banned[self.site].remove(banned_user)
        with open("bannedUsers.txt", "w") as f:
            pickle.dump(self.banned, f)
        return "User @%s has been unbanned." % user_name
    
    def command_listcommands(self, args, msg, event):
        command_keys = self.commands.keys()
        command_keys.sort()
        return "Commands: %s" % (", ".join(command_keys),)

    def command_help(self, args, msg, event):
        if len(args) == 0:
            return "I'm %s, %s's chatbot. You can find the source code [on GitHub](https://github.com/ProgramFOX/SE-Chatbot). You can get a list of all commands by running `>>listcommands`, or you can run `>>help command` to learn more about a specific command." % (self.chatbot_name, self.owner_name)
        command_to_look_up = args[0]
        if command_to_look_up in CommandHelp:
            return CommandHelp[command_to_look_up]
        elif command_to_look_up in self.commands or \
             command_to_look_up in self.owner_commands or command_to_look_up in self.privileged_commands:
            return "Command exists, but no help entry found."
        else:
            return "The command you want to look up, does not exist."

    def command_delete(self, args, msg, event):
        if len(args) == 0:
            return "Not enough arguments."
        try:
            message_id = int(args[0])
        except:
            return "Invalid arguments."
        message_to_delete = Message(message_id, self.client)
        try:
            message_to_delete.delete()
        except:
            pass


    def command_translationchain(self, args, msg, event):
        if event.user.id not in self.owner_ids:
            return "The `translationchain` command is a command that posts many messages and it does not post all messages, and causes that some messages that have to be posted after the chain might not be posted, so it is an owner-only command now."
        if len(args) < 4:
            return "Not enough arguments."
        try:
            translation_count = int(args[0])
        except ValueError:
            return "Invalid arguments."
        if translation_count < 1:
            return "Invalid arguments."
        if not self.translation_chain_going_on:
            if not args[1] in self.translation_languages or not args[2] in self.translation_languages:
                return "Language not in list. If the language is supported, ping ProgramFOX and he will add it."
            self.translation_chain_going_on = True
            thread.start_new_thread(self.translationchain, (args[3], args[1], args[2], translation_count))
            return "Translation chain started. Translation made by [Google Translate](https://translate.google.com). Some messages in the chain might not be posted due to a reason I don't know."
        else:
            return "There is already a translation chain going on."

    def command_translationswitch(self, args, msg, event):
        if event.user.id not in self.owner_ids:
            return "The `translationswitch` command is a command that posts many messages and it does not post all messages, and causes that some messages that have to be posted after the chain might not be posted, so it is an owner-only command now."
        if self.translation_switch_going_on:
            return "There is already a translation switch going on."
        if len(args) < 4:
            return "Not enough arguments."
        try:
            translation_count = int(args[0])
        except ValueError:
            return "Invalid arguments."
        if translation_count < 2:
            return "Invalid arguments."
        if (translation_count % 2) == 1:
            return "Translation count has to be an even number."
        if not args[1] in self.translation_languages or not args[2] in self.translation_languages:
            return "Language not in list. If the language is supported, ping ProgramFOX and he will add it."
        self.translation_switch_going_on = True
        thread.start_new_thread(self.translationswitch, (args[3], args[1], args[2], translation_count))
        return "Translation switch started. Translation made by [Google Translate](https://translate.google.com). Some messages in the switch might not be posted due to a reason I don't know."

    def command_translate(self, args, msg, event):
        if len(args) < 3:
            return "Not enough arguments."
        if args[0] == args[1]:
            return "There's no point in having the same input language as output language."
        if not args[0] in self.translation_languages or not args[1] in self.translation_languages:
            return "Language not in list. If the language is supported, ping ProgramFOX and he will add it."
        return self.translate(args[2], args[0], args[1])

    def translationchain(self, text, start_lang, end_lang, translation_count):
        i = 0
        curr_lang = start_lang
        next_lang = None
        curr_text = text
        choices = list(self.translation_languages)
        if start_lang == end_lang:
            choices.remove(start_lang)
        else:
            choices.remove(start_lang)
            choices.remove(end_lang)
        while i < translation_count - 1:
            if next_lang is not None:
                curr_lang = next_lang
            while True:
                next_lang = random.choice(choices)
                if next_lang != curr_lang:
                    break
            result = self.translate(curr_text, curr_lang, next_lang)
            curr_text = result
            self.room.send_message("Translate %s-%s: %s" % (curr_lang, next_lang, result))
            i += 1
        final_result = self.translate(curr_text, next_lang, end_lang)
        self.room.send_message("Final translation result (%s-%s): %s" % (next_lang, end_lang, final_result))
        self.translation_chain_going_on = False

    def translationswitch(self, text, lang1, lang2, translation_count):
        i = 1
        curr_text = text
        while i <= translation_count:
            if (i % 2) == 0:
                lang_order = (lang2, lang1)
            else:
                lang_order = (lang1, lang2)
            curr_text = self.translate(curr_text, lang_order[0], lang_order[1])
            msg_text = "Translate %s-%s: %s" if i != translation_count else "Final result (%s-%s): %s"
            self.room.send_message(msg_text % (lang_order + (curr_text,)))
            i += 1
        self.translation_switch_going_on = False

    def translate(self, text, start_lang, end_lang):
        translate_url = "https://translate.google.com/translate_a/single?client=t&sl=%s&tl=%s&hl=en&dt=bd&dt=ex&dt=ld&dt=md&dt=qc&dt=rw&dt=rm&dt=ss&dt=t&dt=at&dt=sw&ie=UTF-8&oe=UTF-8&prev=btn&srcrom=1&ssel=0&tsel=0&q=%s" % (start_lang, end_lang, urllib.quote_plus(text.encode("utf-8")))
        r = requests.get(translate_url)
        unparsed_json = r.text.split("],[\"\",,", 1)[0].split("]]", 1)[0][3:]
        return self.parse(unparsed_json)

    def parse(self, json):
        is_open = False
        is_backslash = False
        is_translation = True
        all_str = []
        curr_str = []
        for c in json:
            if c != '"' and not is_open:
                continue
            elif c == '"' and not is_open:
                is_open = True
            elif c == '\\':
                is_backslash = not is_backslash
                if is_translation:
                    curr_str.append(c)
            elif c == '"' and is_open and not is_backslash:
                is_open = False
                if is_translation:
                    s = "".join(curr_str).replace("\\\\", "\\").replace("\\\"", "\"")
                    all_str.append(s)
                curr_str = []
                is_backslash = False
                is_translation = not is_translation
            else:
                is_backslash = False
                if is_translation:
                    curr_str.append(c)
        return " ".join(all_str)
