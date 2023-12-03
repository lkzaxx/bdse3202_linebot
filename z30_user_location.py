# 25.03413655927905, 121.54343435506429


def UserCoordinate():
    user_latitude = 25.03413655927905
    user_longitude = 121.54343435506429
    user_coordinate = f"{user_latitude},{user_longitude}"
    return user_coordinate


if __name__ == "__main__":
    user_coordinate = UserCoordinate()
    print(user_coordinate)
