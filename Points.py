Points = {
	# "username": 100
	# Format is key username, value points
}

def change_points(user, amount):
	if hasattr(Points, user):
		if (Points.user + amount) < 0:
			return ""
	else:
		setattr(Points, user, amount)

