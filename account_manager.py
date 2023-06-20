import dataset_manager as dm
import format_manager as fm

special_characters = "!@#$%^&*()-+?_=,<>/"
current_id = None
is_admin = False
current_user = dict(id=str, username=str, password=str, address=str, city=str, orders=list[str], favorites=list[str], balance=float)
tries_ = 3


def signup():
    if current_id is not None:
        fm.c_format("$$EUser already logged in. Please log off before attempting to sign up a new account.")
        return
    fm.c_format("Signing Up: Please enter the following fields to proceed $$i(fields with$$r$$[ * $$i$$$are mandatory)")
    username = fm.c_input("$$r[*]$$$username: ")
    while not dm.check_username_validity(username):
        fm.c_format("$$eUsername taken. Please enter a new one")
        username = fm.c_input("$$r[*]$$$username: ")

    password = fm.c_input("$$r[*]$$$password: ")
    while len(password) < 8 or not any(c in special_characters for c in password):
        fm.c_format("$$ePassword must be at least 8 characters long and include at least 1 special character")
        password = fm.c_input("$$r[*]$$$password: ")
    fm.c_format("$$F$$bMandatory fields complete. Please fill out these optional fields as well, or skip to account login")
    fm.c_format("$$F$$bYou can fill these optional fields at a later date")
    ad = fm.c_input("address: ")
    city = fm.c_input("city: ")
    user = dict(
        id=dm.get_valid_id(8),
        username=username,
        password=hash(password),
        address=ad,
        city=city,
        orders="",
        favorites="",
        balance=0
    )
    dm.import_user(user)
    fm.c_format("$$gSignup Successfully Completed")


def login(tries=3, username_autofill=None, password_autofill=None):
    global tries_
    fm.c_format("Logging In. Please enter username and password. You have $$e"+str(tries)+"$$$ tries remaining.")
    global current_id, is_admin, current_user
    if current_id is not None:
        fm.c_format("$$eAccount already logged in. Please log off before attempting to log back in")
        return
    while tries > 0:
        tries -= 1

        if username_autofill is not None:
            username = username_autofill
        else:
            username = fm.c_input("username: ")
        if password_autofill is not None:
            password = password_autofill
        else:
            password = fm.c_input("password: ")

        # checking if and where username exists in database
        if dm.check_username_validity(username):  # name does not exist
            fm.c_format("$$eUsername or Password Incorrect. Please try again.\ntries remaining: " + str(tries))
            continue
        if not dm.check_username_validity(username, dm.users['username'].values.tolist()):  # checking for users
            admin = False
            user = dm.retrieve_user(username)
            if user is None:
                fm.c_format("$$EError retrieving user's account. Please try again.\ntries remaining: " + str(tries))
                continue
        else:
            if not dm.check_username_validity(username, dm.admins['username'].values.tolist()):  # checking for admins
                admin = True
                user = dm.retrieve_admin(username)
                if user is None:
                    fm.c_format("$$EError retrieving user's account. Please try again.\ntries remaining: " + str(tries))
                    continue
            else:  # failsafe
                fm.c_format("$$eUsername or Password Incorrect. Please try again.\ntries remaining: " + str(tries))
                continue
        # checking password
        if check_password(username, password):
            fm.c_format("$$gSuccessfully logged in. Welcome {}{}$$g!".format("$$y" if admin else "$$c", username))
            tries_ = 3
            current_id = user.get('id')
            is_admin = admin
            current_user = user
            return
        fm.c_format("$$eUsername or Password Incorrect. Please try again.\ntries remaining: "+str(tries))
    fm.c_format("$$EToo many unsuccessful attempts. Please try again later.")
    exit()


def logout():
    global current_id, is_admin
    if current_id is None:
        fm.c_format("$$eNo user currently logged in to log out. Please log in first")
        return
    if is_admin:
        user = dm.retrieve_admin(current_id)
    else:
        user = dm.retrieve_user(current_id)
    if user is not None:
        fm.c_format("$$gUser {}{}$$g has successfully logged out. See you again soon!".format(
            "$$y" if is_admin else "$$c", user.get('username')))
    else:
        fm.c_format("$$gUser $$$$$r$$~unknown$$$$$g successfully logged out. See you again soon!")
    current_id = None
    is_admin = False


def check_password(username, password):
    user = dm.retrieve_user(username)
    if user is None:
        user = dm.retrieve_admin(username)
        if user is None:
            return False
    return hash(password) == int(user['password'])
