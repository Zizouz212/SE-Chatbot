Points = {
    # "username": 100
    # Format is key username: value points
}

def change_points(user, amount):
    if user not in Points:
        Points[user] = 0
    if (Points[user] + amount) < 0:
        return "Can't perform an action that would take the total for " + user + " under 0."
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
    
    result = change_points(user, amount)
    change_points(negUser, negAmount)
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
        return "0"

