Points = {
	# "username": 100
	# Format is key username: value points
}

def change_points(user, amount):
	if not hasattr(Points, user):
		setattr(Points, user, 0)
	if (Points.user + amount) < 0:
		return "Can't perform an action that would take the total for " + user + " under 0."
	else:
		Points.user += amount
		return "Changed points for " + user + " by " + str(amount) + ". New total: " + str(Points.user)
		
def give_points(args, msg, event):
	if len(args) < 4:
		return "Not enough arguments."
	
	user = args[2]
	amount = args[3]
	
	if str_contains(amount, "-"):
		return "You cannot take points from another user."
	try:
		amount = int(amount)
	except:
		return "Invalid amount."
	
	negAmount = -amount;
	negUser = event.user.name
	
	change_points(user, amount)
	change_points(negUser, negAmount)
	
def get_points(args, msg, event):
	user = ""
	if len(args) == 2:
		user = event.user.name
	elif len(args) >= 3:
		user = args[2]
	if hasattr(Points, user):
		return Points.user
	else:
		return 0

def str_contains(str, needle):
	chars = str.split("")
	for i in range len(chars):
		if chars[i] == needle:
			return True
	return False
