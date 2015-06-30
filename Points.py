from Config import Config
import SaveIO

Points = {
    # "username": 100
    # Format is key username: value points
    "KarmaBot": 9999999999999999999999
}

def init():
    global Points
    Points = SaveIO.load(SaveIO.path)

def close():
    global Points
    SaveIO.save(SaveIO.path, Points)

def change_points(user, amount):
    if user not in Points:
        Points[user] = 200
    if (Points[user] + amount) < 0:
        return False
    else:
        Points[user] += amount
        return "Changed points for " + user + " by " + str(amount) + ". New total: " + str(Points[user])
        
def give_points(args, msg, event):
    if len(args) < 3:
        return "Not enough arguments."
    
    user = args[1]
    amount = args[2]
    
    if "-" in amount:
        return "You cannot take points from a user."
    try:
        amount = int(amount)
    except:
        return "Invalid amount."
    
    negAmount = -amount;
    negUser = event.user.name
    
    remove = change_points(negUser, negAmount)
    if remove == False:
        return "You do not have enough points to give that many away."
    result = change_points(user, amount)
    return result
    
def admin_points(args, msg, event):
    if event.user.id not in Config.General["owners"]:
		return "You don't have permission to administrate points."
    
    if len(args) < 3:
        return "Not enough arguments."
    
    user = args[1]
    amount = args[2]
    
    try:
        amount = int(amount)
    except:
        return "Invalid amount."

    result = change_points(user, amount)
    return result
    
def get_points(args, msg, event):
    user = ""
    if len(args) == 1:
        user = event.user.name
    elif len(args) >= 2:
        user = args[1]
    if user in Points:
        return str(Points[user])
    else:
        Points[user] = 200
        return "200"

