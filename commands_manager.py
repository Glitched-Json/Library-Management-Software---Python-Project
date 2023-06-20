import account_manager as am
import dataset_manager as dm
import format_manager as fm
import pandas as pd
import matplotlib.pyplot as mp
from collections import defaultdict
from random import sample
import os.path

command_key = '!'
for_admins: dict
for_users: dict
commons: dict
disconnected: dict
always: dict


def __calculate_commands(key):
    global for_admins, for_users, commons, disconnected, always, command_key
    command_key = key
    for_admins = {command_key + "graph_table": make_graphic_table,
                  command_key + "check_availability": check_availability,
                  command_key + "export_csv": export_csv,
                  command_key + "delete_book": delete_book,
                  command_key + "delete_user": delete_user,
                  command_key + "edit_book": edit_book}
    for_users = {command_key + "recommendations": get_book_recommendations,
                 command_key + "transfer_balance": transfer_balance,
                 command_key + "user": edit_personal_data,
                 command_key + "rate_book": rate_book}
    commons = {command_key + "view_ratings": view_ratings,
               command_key + "import_books": import_book_list,
               command_key + "import_book": import_book,
               command_key + "logout": am.logout}
    disconnected = {
               command_key + "login": am.login,
               command_key + "signup": am.signup,
               command_key + "exit": ""}
    always = {
        "change_command_key": change_command_key,
        command_key + "help": print_commands
    }


def run_console():
    while True:
        print_commands()
        command = fm.c_input("Waiting Entry: ")
        if command not in get_command_access().keys():
            fm.c_format("$$eInvalid command '"+command+"'")
            continue
        if command == command_key + "exit":
            break
        get_command_access()[command]()


def get_command_access():
    if am.current_id is None:
        return {**disconnected, **always}
    if am.is_admin:
        return {**for_admins, **commons, **always}
    return {**for_users, **commons, **always}


def print_commands():
    fm.c_format("Available commands: $$i$$c{}".format(", ".join(get_command_access())))


def get_book_recommendations():
    if not _is_user():
        return

    entries_shown = 5
    mask_ids = am.current_user['favorites'] + am.current_user['orders']
    if not mask_ids:
        mask_ids = []

    # find highest(s) categories within favorites list
    favorites = [x['categories'] for x in map(dm.retrieve_book, am.current_user['favorites']) if x is not None]
    data = defaultdict(int)
    for categories in favorites:
        for category in categories:
            data[category] += 1
    data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    data = [x[0] for x in data if x[1] is data[0][1]]

    # make recommendations list
    books = dm.books[~dm.books['id'].isin(mask_ids)].to_dict('records')
    recommendations = [x['id'] for x in books if all(cat in x['categories'] for cat in data)]
    if len(recommendations) < entries_shown:
        if len(data) > 1:
            recommendations = recommendations + [x['id'] for x in books if any(cat in x['categories'] for cat in data) and x['id'] not in recommendations]
        if len(recommendations) < entries_shown:
            recommendations = recommendations + sample(
                [x['id'] for x in dm.books[~dm.books['id'].isin(mask_ids + recommendations)].to_dict('records')],
                entries_shown - len(recommendations))
    if len(recommendations) > entries_shown:
        recommendations = sample(recommendations, entries_shown)

    # show recommendations
    for book in recommendations:
        b = dm.retrieve_book(book)
        fm.c_format("$$i$$p[{}]$$$ - {} - $$i({})$$$ - $$[ {} $$$".format(
            book, b['title'], ", ".join(b['categories']), b['cost']))


def transfer_balance():
    if not _is_user():
        return

    while True:
        inp = fm.c_input("Enter amount to be transferred from card to balance $$i(leave blank to go back)$$$: ")
        if not inp:
            return
        if not is_float(inp):
            fm.c_format("$$eAmount must be a positive number. Please enter a new amount.")
            continue
        if float(inp) <= 0:
            fm.c_format("$$eAmount must be a positive number. Please enter a new amount.")
            continue
        break
    dm.update_attribute('balance', str(float(am.current_user['balance']) + float(inp)), am.current_id)
    am.current_user = dm.retrieve_user(am.current_id)
    fm.c_format("$$g{:.2f} have been successfully added to your account.".format(float(inp)))


def edit_personal_data():
    if not _is_user():
        return

    user = am.current_user
    dm.__save_dataframes()

    while True:
        # select category
        dm.print_formatted(user, 2)
        while True:
            category = fm.c_input("$$r[*]$$$Category $$i(Leave blank to go back)$$$: ")
            if category in dm.users.columns:
                if category == 'id' or category == 'balance':
                    fm.c_format("$$EImmutable Category. Please enter a category again.")
                    continue
                break
            if not category:
                fm.c_format("$$i$$b$$FExiting Edit_Personal_Data function")
                return
            fm.c_format("$$eInvalid Category. Please enter a category again.")
        while True:
            val = user[category]
            if category in dm.compressed_keys:  # orders, favorites
                cat = category == "orders"
                # print category values and indices
                if not val:
                    fm.c_format("\t0 - ")
                else:
                    fm.c_format(category + ": ")
                    for i, v in enumerate(val):
                        fm.c_format("\t{} - [{}]{}".format(
                            i,
                            v,
                            " - $$i$$[{} $$$ - {}".format(dm.get_overall_rating(v), dm.retrieve_book(v)['title'])
                            if dm.retrieve_book(v) is not None else ""
                        ))
                    fm.c_format("\t{} - ".format(len(val)))
                # selecting data user wants to edit
                fm.c_format("Please enter the index of the value you want to edit or Leave blank to go back "
                            "$$i(enter $$c{}clear$$$$$i to clear your list)$$$.".format(command_key))
                while True:
                    inp = fm.c_input("Index: ")
                    if inp == command_key + "clear":
                        dm.update_attribute(category, [], user['id'])
                        if cat:
                            cost = 0
                            for book_id in val:
                                cost += float(dm.retrieve_book(book_id)['cost']) if dm.retrieve_book(book_id) is not None else 0
                            dm.update_attribute('balance', str(float(user['balance']) + cost), user['id'])
                            fm.c_format("$$y{:.2f}$$g have been added to your account.".format(cost))
                        user = am.current_user = dm.retrieve_user(am.current_id)
                        fm.c_format("$$gList Cleared Successfully. $$$")
                        break
                    if not inp:
                        break
                    while not is_int(inp):
                        inp = fm.c_input("Index $$i(whole numbers only)$$$: ")
                    if int(inp) < 0 or int(inp) > len(val):
                        fm.c_format("$$eIndex '" + inp + "' outside of range [0, " + str(
                            len(val)) + "]. Please enter a new index.")
                        continue
                    break
                if not inp or inp == command_key + "clear":
                    break
                # retrieving new value  val[int(inp)]
                extra_val = False
                if int(inp) == len(val):
                    extra_val = True
                    val.append("")
                fm.c_format("Editing Value: {}{}".format(
                    "[" + val[int(inp)] + "]" if val[int(inp)] else "",
                    " - " + dm.retrieve_book(val[int(inp)])['title'] if dm.retrieve_book(val[int(inp)]) is not None else ""
                ))
                while True:
                    new_val = fm.c_input("Enter book's id/title "
                                         "$$i(Extra available commands: $$c{}new_book{}$$$$$i)$$$: ".format(
                                            command_key,
                                            ", {k}add_rating, {k}cancel".format(k=command_key) if not extra_val else ""))
                    if new_val == command_key + "new_book":
                        new_val = import_book()
                        break
                    if new_val == command_key + "add_rating" and not extra_val:
                        rate_book(int(inp))
                        break
                    if new_val == command_key + "cancel" and not extra_val:
                        break
                    new_val = new_val.strip()
                    if not new_val:
                        break
                    if dm.retrieve_book(new_val) is None:
                        fm.c_format("$$eBook with id/title '" + new_val + "' was not found within the system. Please enter a new value.")
                        continue
                    break
                if new_val == command_key + "add_rating" or new_val == command_key + "cancel":
                    continue
                # updating entry
                cost: float = 0
                if not extra_val:
                    if cat:
                        book = dm.retrieve_book(val[int(inp)])
                        if book is not None:
                            cost = -float(book['cost'])
                if new_val:
                    book = dm.retrieve_book(new_val)
                    if not cat:
                        val[int(inp)] = dm.retrieve_book(new_val)['id']
                    elif float(user['balance'])-cost >= float(book['cost']):
                        if -cost > 0:
                            fm.c_format("$$y{:.2f}$$g have been added to your account.".format(-cost))
                        cost += float(book['cost'])
                        val[int(inp)] = dm.retrieve_book(new_val)['id']
                        fm.c_format("$$gYou added the book '{}' in your orders list for $$y{:.2f}".format(
                            book['title'], float(book['cost'])
                        ))
                    else:
                        fm.c_format("$$eInsufficient funds to add this to your orders list."
                                    "\n\t$$i(book's cost: $$y{:.2f}$$$$$i, your balance: $$y{:.2f}$$$$$i)"
                                    .format(float(book['cost']), float(user['balance'])))
                        continue
                else:
                    if cat:
                        fm.c_format("$$y{:.2f}$$g have been added to your account.".format(-cost))
                    del val[int(inp)]
                if val:
                    dm.update_attribute(category, val, user['id'])
                else:
                    dm.update_attribute(category, [], user['id'])
                if cat:
                    dm.update_attribute('balance', str(float(user['balance'])-cost), user['id'])
                user = am.current_user = dm.retrieve_user(user['id'])
                fm.c_format("$$gUpdate Successful")
            else:  # username, password, address, city
                fm.c_format("Editing Value: " + (val if category != "password" else "password"))
                if category == 'username':
                    while True:
                        val = fm.c_input("Enter a new username $$i(enter blank to go back)$$$: ").strip()
                        if val in dm.usernames:
                            fm.c_format("$$eThis username is already taken. Please enter a new one")
                            continue
                        break
                    if not val:
                        break
                elif category == 'password':
                    while am.tries_ > 0:
                        fm.c_format("Please enter your password again. You have $$e"+str(am.tries_)+"$$$ tries remaining.")
                        pw = fm.c_input("$$r[*]$$$password: ")
                        if am.check_password(user['username'], pw):
                            break
                        am.tries_ -= 1
                    if am.tries_ == 0:
                        fm.c_format("$$EToo many unsuccessful attempts. Please try again later.")
                        exit()

                    while True:
                        val = fm.c_input("Enter the new value $$i(leave blank to go back)$$$: ").strip()
                        if not val:
                            break
                        if len(val) < 8 or not any(c in am.special_characters for c in val):
                            fm.c_format("$$ePassword must be at least 8 characters long and include at least 1 special character")
                            continue
                        break
                    if not val:
                        break
                    val = hash(val)
                else:
                    val = fm.c_input("Enter the new value: ").strip()
                dm.update_attribute(category, val, user['id'])
                user = am.current_user = dm.retrieve_user(user['id'])
                fm.c_format("$$gUpdate Successful$$$")
                break
        if not val:
            continue


def make_graphic_table(mode="+"):
    # user checks
    if not _is_admin():
        return

    while mode not in ['publisher', 'author', 'category', 'bookstore', 'cost', 'city', '']:
        mode = fm.c_input("Enter mode or leave blank to go back $$c$$i(publisher, author, category, bookstore, cost, city)$$$: ")
    if not mode:
        return

    if mode == "publisher":
        data = dict.fromkeys(dm.books.publisher.unique(), 0)
        for book in dm.books.to_dict("records"):
            data[book['publisher']] += int(book['copies'])
        courses = list(data.keys())
        values = list(data.values())
        mp.bar(courses, values, color='maroon', width=0.8)
        mp.xlabel("Publishers")
        mp.ylabel("No. of books (including copies)")
        mp.title("Number of books publishers have (including copies)")
        mp.show()
        return
    if mode == "author":
        data = dict.fromkeys(dm.books.author.unique(), 0)
        for book in dm.books.to_dict("records"):
            data[book['author']] += 1
        courses = list(data.keys())
        values = list(data.values())
        mp.bar(courses, values, color='maroon', width=0.8)
        mp.xlabel("Authors")
        mp.ylabel("No. of books (not including copies)")
        mp.title("Number of books authors have written")
        mp.show()
        return
    if mode == "category":
        data = defaultdict(int)
        for book in dm.books.to_dict("records"):
            for category in book['categories']:
                data[category] += 1
        courses = list(data.keys())
        values = list(data.values())
        mp.bar(courses, values, color='maroon', width=0.8)
        mp.xlabel("Categories")
        mp.ylabel("No. of books (not including copies)")
        mp.title("Number of books per category")
        mp.show()
        return
    if mode == "bookstore":
        data = defaultdict(int)
        for book in dm.books.to_dict("records"):
            for store in book['bookstores']:
                data[store] += int(book['copies'])
        courses = list(data.keys())
        values = list(data.values())
        mp.bar(courses, values, color='maroon', width=0.8)
        mp.xlabel("Bookstores")
        mp.ylabel("No. of books (including copies)")
        mp.title("Number of books per bookstore (including copies)")
        mp.show()
        return
    if mode == "cost":
        data: dict[float, int] = defaultdict(int)
        for book in dm.books.to_dict("records"):
            data[float(book['cost'])] += 1
        x = list(data.keys())
        x.sort()
        data = {i: data[i] for i in x}
        mp.plot(list(data.keys()), data.values())
        mp.xlabel("Cost")
        mp.ylabel("No. of books")
        mp.title("Books Cost Distribution")
        mp.show()
        return
    if mode == "city":
        data = dict.fromkeys(dm.users.city.unique(), 0)
        for user in dm.users.to_dict("records"):
            data[user['city']] += 1
        courses = list(data.keys())
        values = list(data.values())
        mp.bar(courses, values, color='maroon', width=0.8)
        mp.xlabel("Cities")
        mp.ylabel("No. of users")
        mp.title("Number of users per city")
        mp.show()
        return


def check_availability():
    # user checks
    if not _is_admin():
        return

    while True:
        inp = fm.c_input("Please Enter the book's id or title $$i(Enter nothing to go back)$$$: ")
        if not inp:
            return
        book = dm.retrieve_book(inp)
        if book is None:
            fm.c_format("$$eBook's id/title not found in the system. Please enter a new value.")
            continue
        break
    fm.c_format("The book $$c$$i'" + book['title'] + "'$$$ is available in these bookstores:"
                " \n\t$$c$$i" + ", ".join(book['availability']))


def export_csv(file="+", output=""):
    # user checks
    if not _is_admin():
        return
    # mode checks
    while file not in ['users', 'admins', 'books', '']:
        file = fm.c_input("Enter mode or leave blank to go back $$i$$c(users, admins, books)$$$: ")
    if not file:
        return
    if not output:
        output = fm.c_input("Enter filename: ") + ".csv"
    # export users
    if file == 'users':
        f = dm.users.copy()
        f['password'] = '-'
        f.to_csv(output)
        fm.c_format("$$F$$b$$iExported users to file " + output)
        return

    # export admins
    if file == 'admins':
        f = dm.admins.copy()
        f['password'] = '-'
        f.to_csv(output)
        fm.c_format("$$F$$b$$iExported admins to file " + output)
        return

    # export admins
    if file == 'books':
        dm.books.to_csv(output)
        fm.c_format("$$F$$b$$iExported books to file " + output)
        return


def delete_book():
    # user checks
    if not _is_admin():
        return
    bookstores = am.current_user['bookstores']
    while True:
        inp = fm.c_input("Please Enter the book's id or title $$i(Enter nothing to go back)$$$: ")
        if not inp:
            return
        book = dm.retrieve_book(inp)
        if book is None:
            fm.c_format("$$eBook's id/title not found in the system. Please enter a new value.")
            continue
        if not [v for v in bookstores if v in book['bookstores']]:
            fm.c_format("$$eYou do not have access to any of the libraries this book is housed in. Please enter a new value.")
            continue
        break
    removed = [x for x in book['bookstores'] if x in bookstores]
    libs = [x for x in book['bookstores'] if x not in bookstores]
    if libs:
        dm.update_attribute('bookstores', libs, book['id'])
        fm.c_format("$$gDeleted book $$c$$i'" + book['title'] + "'$$$$$g from these bookstores:")
        fm.c_format("$$c$$i" + ", ".join(removed))
        availabilities = [x for x in book['availability'] if x not in bookstores]
        dm.update_attribute('availability', availabilities, book['id'])
        return
    dm.delete_entry(book['id'])
    fm.c_format("$$gBook $$c$$i'{}'$$$$$g has been successfully deleted from the system.$$$".format(book['title']))


def delete_user():
    # user checks
    if not _is_admin():
        return

    while True:
        inp = fm.c_input("Please Enter the user's id or username $$i(Enter nothing to go back)$$$: ")
        if not inp:
            return
        user = dm.retrieve_user(inp)
        if user is None:
            fm.c_format("$$eUser's id/username not found in the system. Please enter a new value.")
            continue
        break
    dm.delete_entry(user['id'])
    fm.c_format("$$gUser $$c'{}'$$g has been successfully deleted$$$".format(user['username']))


def edit_book(input_book=None):
    # user checks
    if not _is_admin():
        return
    bookstores = am.current_user['bookstores']

    # retrieving book admin wants to edit
    if input_book is not None:
        book = dm.retrieve_book(input_book)
        if not [v for v in bookstores if v in book['bookstores']]:
            fm.c_format("$$eYou do not have access to any of the libraries this book is housed in")
            return
    else:
        while True:
            inp = fm.c_input("Please Enter the book's id or title $$i(Enter nothing to go back)$$$: ")
            if not inp:
                return
            book = dm.retrieve_book(inp)
            if book is None:
                fm.c_format("$$eBook's id/title not found in the system. Please enter a new value.")
                continue
            if not [v for v in bookstores if v in book['bookstores']]:
                fm.c_format("$$eYou do not have access to any of the libraries this book is housed in. Please enter a new value.")
                continue
            break

    # editing book
    while True:
        if not [v for v in bookstores if v in book['bookstores']]:
            fm.c_format("$$eYou no longer have access to any of the libraries this book is housed in.")
            break
        dm.print_formatted(book, 2)
        fm.c_format("Select one of the categories from the above to alter.")
        while True:
            category = fm.c_input("$$r[*]$$$Category $$i(Leave blank to go back)$$$: ")
            if category in dm.books.columns:
                if category == 'id':
                    fm.c_format("$$EImmutable Category. Please enter a category again.")
                    continue
                break
            if not category:
                fm.c_format("$$F$$b$$iExiting Edit_Book function")
                return
            fm.c_format("$$eInvalid Category. Please enter a category again.")
        # showing value(s) inside the category
        while True:
            val = book[category]
            if category == 'ratings':  # ratings
                # print category values and indices
                if not val:
                    fm.c_format("$$eThis book has no ratings yet.")
                    break
                else:
                    fm.c_format(category + ": ")
                    for i, v in enumerate(val):
                        dm.print_formatted_rating(v, "\t$$g"+str(i)+"$$$ --- ", True)
                # selecting the specific rating the admin wants to edit
                fm.c_format("Please enter the index of the rating you want to view $$i(Leave blank to go back)$$$.")
                while True:
                    inp = fm.c_input("Index: ")
                    if not inp:
                        break
                    while not is_int(inp):
                        inp = fm.c_input("Index $$i(whole numbers only)$$$: ")
                    if int(inp) < 0 or int(inp) >= len(val):
                        fm.c_format("$$eIndex '" + inp + "' outside of range [0, " +
                                    str(len(val)-1) + "]. Please enter a new index.")
                        continue
                    break
                if not inp:
                    break
                # showing the entire rating
                while True:
                    comments = dm.print_formatted_rating(val[int(inp)], "", False, True)
                    fm.c_format("\t[{}] - ".format(len(comments)))
                    fm.c_format("Please enter the index of the value you want to edit or leave blank to go back."
                                "$$i(Available Commands: $$c{}delete$$$$$i)$$$.".format(command_key))
                    while True:
                        inp2 = fm.c_input("Index: ")
                        if not inp2:
                            break
                        if inp2 == command_key + 'delete':
                            del val[int(inp)]
                            fm.c_format("$$gRating Successfully Deleted")
                            break
                        while not is_int(inp2):
                            inp2 = fm.c_input("Index $$i(whole numbers only)$$$: ")
                        if int(inp2) < 0 or int(inp2) > len(comments):
                            fm.c_format("$$eIndex '" + inp2 +
                                        "' outside of range [0, " + str(len(val)) + "]. Please enter a new index.")
                            continue
                        break
                    if not inp2 or inp2 == command_key + 'delete':
                        break
                    new_comment = fm.c_input("Enter edited comment: ").strip()
                    if int(inp2) == len(comments):
                        if new_comment:
                            comments.append(new_comment)
                    else:
                        if new_comment:
                            comments[int(inp2)] = new_comment
                        else:
                            del comments[int(inp2)]
                    rating = val[int(inp)]
                    val[int(inp)] = [rating[0], str(am.current_id), rating[2]] + comments
                    dm.update_attribute('ratings', val, book['id'])
                    book = dm.retrieve_book(book['id'])
                    fm.c_format("$$gUpdate Successful$$$")
                if not inp:
                    break

            elif category in dm.compressed_keys:  # bookstores, availability, categories
                if not [v for v in bookstores if v in book['bookstores']]:
                    break
                cat = category == "categories"
                # print category values and indices
                if not val:
                    val = ['']
                    fm.c_format("\t$$g0$$$ --- ")
                else:
                    val.append('')
                    fm.c_format(category + ": ")
                    for i, v in enumerate(val):
                        access = v in bookstores or not v or cat
                        fm.c_format("\t" + ("$$g" if access else "$$r") + str(i) + "$$$ -" + ("-" if access else "/") + "- $$i" + v)
                # selecting the specific value the admin wants to edit
                fm.c_format("Please enter the index of the value you want to edit $$i(Leave blank to go back)$$$.")
                while True:
                    inp = fm.c_input("Index: ")
                    if not inp:
                        if len(val) > 1:
                            del val[-1]
                        else:
                            val = []
                        break
                    while not is_int(inp):
                        inp = fm.c_input("Index $$i(whole numbers only)$$$: ")
                    if int(inp) < 0 or int(inp) > len(val):
                        fm.c_format("$$eIndex '" + inp + "' outside of range [0, " + str(
                            len(val)) + "]. Please enter a new index.")
                        continue
                    break
                if not inp:
                    break
                # checking if the entry being edited can be accessed by the admin
                if int(inp) < len(val) - 1 and val[int(inp)] not in bookstores and not cat:
                    fm.c_format("$$eYou do not have access to the library $$$$$c$$i'" + val[int(inp)] + "'$$$$$e. "
                                "You can only alter bookstore/availability options for libraries you have access to.")
                    fm.c_format("$$c$$i"+", ".join(bookstores))
                    continue
                # retrieving new value
                fm.c_format("Editing Value: $$i" + val[int(inp)] + "$$$")
                new_val = fm.c_input("Enter the new value: ").strip()
                if new_val not in bookstores and new_val and not cat:
                    fm.c_format("$$eYou do not have access to the library '" + new_val + "'."
                                "You can only alter bookstore/availability options for libraries you have access to.")
                    print(bookstores)
                    continue
                # updating entry
                val[int(inp)] = new_val
                if int(inp) < len(val) - 1:
                    del val[-1]
                if not val[int(inp)]:
                    del val[int(inp)]
                if val:
                    dm.update_attribute(category, val, book['id'])
                    if category == "bookstores":
                        availabilities = [x for x in book['availability'] if x in val]
                        dm.update_attribute('availability', availabilities, book['id'])
                else:
                    dm.update_attribute(category, '', book['id'])
                    if category == "bookstores":
                        dm.delete_entry(book['id'])
                        return
                book = dm.retrieve_book(book['id'])
                fm.c_format("$$gUpdate Successful$$$")

            else:  # title, author, publisher, cost, copies
                fm.c_format("Editing Value: $$i" + val + "$$$")
                if category == 'copies':
                    while True:
                        val = fm.c_input("Enter the new value: ").strip()
                        if not is_int(val):
                            fm.c_format("$$eValue must be a whole non-negative number.")
                            continue
                        if int(val) < 0:
                            fm.c_format("$$eValue must be a whole non-negative number.")
                            continue
                        break
                elif category == 'cost':
                    while True:
                        val = fm.c_input("Enter the new value: ").strip()
                        if not is_float(val):
                            fm.c_format("$$eValue must be a non-negative number.")
                            continue
                        if float(val) < 0:
                            fm.c_format("$$eValue must be a non-negative number.")
                            continue
                        break
                else:
                    val = fm.c_input("Enter the new value: ").strip()
                dm.update_attribute(category, val, book['id'])
                book = dm.retrieve_book(book['id'])
                fm.c_format("$$gUpdate Successful$$$")
                break
            if not inp:
                break


def import_book_list():
    if am.current_id is None:
        fm.c_format("$$eNo user logged in. Please log in first.")
        return
    # get file
    while True:
        file = fm.c_input("Enter the name of a .csv file to import the books from $$i(leave blank to go back)$$$: ")
        if not file:
            return
        if not os.path.isfile(file):
            fm.c_format("$$eFile location was not found. Please enter a new file name.")
            continue
        if not file.endswith(".csv"):
            fm.c_format("$$eIncorrect file type. Make sure the given file ends in $$[ .csv $$$")
            continue
        break

    if am.is_admin:
        imported_books = pd.read_csv(file).astype(str).to_dict('records')
        bookstores = am.current_user.get('bookstores')
        imported = 0
        for book in imported_books:
            if book['id'] not in dm.ids:
                book.update({'bookstores':
                             [v for v in bookstores if v in book['bookstores']],
                             'availability':
                             [v for v in bookstores if v in book['availability']]})
                dm.import_book(book)
                imported += 1
        if len(imported_books) - imported > 0:
            fm.c_format('$$gFound $$y' + str(len(imported_books) - imported) + '$$g books already in the system.')
        fm.c_format('$$gSuccessfully imported $$y' + str(imported) + '$$g books from file $$i$$c"' + file + '"$$$$$g.$$$')
        return
    # run client line
    favorites_list = am.current_user.get('favorites')
    if len(favorites_list) == 1 and not favorites_list[0]:
        favorites_list = []
    imported_books = pd.read_csv(file).astype(str).to_dict('records')
    imported = 0
    for book in imported_books:
        if book['id'] not in favorites_list:
            if book['id'] not in dm.ids:  # new book entry
                dm.import_book(book)
            favorites_list.append(book['id'])
            imported += 1
    dm.update_attribute('favorites', favorites_list)
    am.current_user = dm.retrieve_user(am.current_id)
    if len(imported_books) - imported > 0:
        fm.c_format('$$gFound $$y' + str(len(imported_books) - imported) + '$$g books already in your favorites list.')
    fm.c_format('$$gSuccessfully imported $$y' + str(imported) + '$$g books from file $$i"' + file + '"$$s to your favorites list.')


def import_book():
    # user logged in detection
    if am.current_id is None:
        fm.c_format("$$eNo user logged in. Please log in first.")
        return
    fm.c_format("Please enter the book's data:")

    # book title input
    while True:
        title = fm.c_input("$$r[*]$$$Title: ").strip()
        if not title:
            fm.c_format("$$F$$b$$iExiting Import_Book Function")
            return
        if title in dm.titles:
            if am.is_admin:
                fm.c_format("$$eA book with this title already exists.")
                return
            book = dm.retrieve_book(title)
            favorites = am.current_user.get('favorites')
            favorites.append(book['id'])
            dm.update_attribute('favorites', favorites)
            am.current_user = dm.retrieve_user(am.current_id)
            fm.c_format("$$eA book with this title already exists, and has been added to your favorites.")
            return
        break

    # book author input
    author = fm.c_input("Author: ").strip()

    # book publisher input
    publisher = fm.c_input("Publisher: ").strip()

    # book categories input
    i = 1
    category = [fm.c_input("Category $$yn" + str(i) + "$$$ $$i(enter nothing to finish selection)$$$: ").strip()]
    while category[-1]:
        i += 1
        category.append(fm.c_input("Category $$yn" + str(i) + "$$$: ").strip())
    category = category[:-1]

    # book cost input (floats only)
    while True:
        cost = fm.c_input("$$r[*]$$$Cost: ")
        if not is_float(cost):
            fm.c_format("$$eValue must be a positive number")
            continue
        if float(cost) <= 0:
            fm.c_format("$$eValue must be a positive number")
            continue
        break
    availability = []
    copies = 0
    bookstores = []
    if am.is_admin:
        # book's available bookstore locations input (admin access only)
        fm.c_format("Enter the bookstores the book will be housed in. These are the available options: ")
        fm.c_format("$$c$$i" + ", ".join(am.current_user.get('bookstores')) + "$$$")
        i = 1
        bookstores = [
            fm.c_input("Bookstore $$yn" + str(i) + "$$$ $$i(enter nothing to finish selection)$$$: ").strip()]
        while bookstores[-1]:
            i += 1
            bookstores.append(fm.c_input("Bookstore $$yn" + str(i) + "$$$: ").strip())
        bookstores = [v for v in bookstores if v in am.current_user.get('bookstores')]

        # book's current availability options (book's bookstore location only)
        fm.c_format("Enter the bookstores in which the book is currently available in. These are the available options: ")
        fm.c_format("$$c$$i" + ", ".join(bookstores) + "$$$")
        i = 1
        availability = [
            fm.c_input("Availability $$yn" + str(i) + "$$$ $$i(enter nothing to finish selection)$$$: ").strip()]
        while availability[-1]:
            i += 1
            availability.append(fm.c_input("Availability $$yn" + str(i) + "$$$: ").strip())
        availability = [v for v in availability if v in bookstores]

        # book's available copies
        while True:
            copies = fm.c_input("$$r[*]$$$Copies: ")
            if not is_int(copies):
                fm.c_format("$$eValue must be a non-negative number")
                continue
            if int(copies) < 0:
                fm.c_format("$$eValue must be a non-negative number")
                continue
            break

    # book creation and handling
    book = dict(id=str(dm.get_valid_id(10)), title=title, author=author, publisher=publisher,
                categories=category, cost=cost, availability=availability, copies=copies,
                bookstores=bookstores, ratings=[])
    dm.import_book(book)
    if am.is_admin:
        fm.c_format("$$gSuccessfully added book with title $$c$$i'" + book['title']
                    + "'$$s$$g and id $$p$$i'" + book['id'] + "'$$s$$g to the database.")
        return
    favorites = am.current_user.get('favorites')
    favorites.append(str(book['id']))
    dm.update_attribute('favorites', favorites)
    am.current_user = dm.retrieve_user(am.current_id)
    fm.c_format("$$gSuccessfully added book with title $$c$$i'" + book['title'] + "'$$s$$g to your favorites.$$$")
    return book['id']


def rate_book(book=-1):
    # user check
    if not _is_user():
        return
    # able to rate at least one book
    orders_list = am.current_user['orders']
    if not orders_list:
        fm.c_format("$$eNo books found in your orders list. You can only rate a book in your orders list.")
        return
    # retrieving book
    while book < 0:
        for i, v in enumerate(orders_list):
            fm.c_format("\t" + str(i) + (" - " + dm.retrieve_book(v)['title'] if dm.retrieve_book(v) is not None else ""))
        book = fm.c_input("Enter the index of the book you want to rate $$i(leave blank to go back)$$$: ")
        if not book:
            return
        if not is_int(book):
            fm.c_format("$$eIndex must be a whole number between [0, {}]. Please enter a new value.".format(len(orders_list)-1))
            book = -1
            continue
        if int(book) < 0 or int(book) >= len(orders_list):
            fm.c_format("$$eIndex must be a whole number between [0, {}]. Please enter a new value.".format(len(orders_list)-1))
            book = -1
            continue
        if dm.retrieve_book(orders_list[int(book)]) is None:
            fm.c_format("$$EError retrieving book. Please enter a new value.")
            book = -1
            continue
        break
    print(int(book))
    print(orders_list[int(book)])
    ratings = dm.retrieve_book(orders_list[int(book)])['ratings']
    print(ratings)
    ind = None
    for i, rating in enumerate(ratings):
        if rating[0] == am.current_id:
            ind = i
            break
    if ind is None:  # adding new rating
        # getting rating
        fm.c_format("$$[ rating 0-10 $$$")
        while True:
            r = fm.c_input("\t$$r[*]$$$Enter Rating $$i(Leave blank to go back)$$$: ")
            if not r:
                return
            if not is_float(r):
                fm.c_format("$$eMust be a number between 0 and 10")
                continue
            if float(r) < 0 or float(r) > 10:
                fm.c_format("$$eMust be a number between 0 and 10")
                continue
            break
        comments = []
        while True:
            fm.c_format("$$[ comments $$$")
            for i, c in enumerate(comments):
                fm.c_format("\t[{}] - $$i{}$$$".format(i, c))
            fm.c_format("\t[{}] - ".format(len(comments)))

            fm.c_format("Enter the index of the comment you want to edit $$i(leave blank to finish rating process)$$$")
            while True:
                val = fm.c_input("Index: ")
                if not val:
                    break
                if not is_int(val):
                    fm.c_format("$$eValue must be a whole number between 0 and " + str((len(comments))))
                    continue
                if int(val) < 0 or int(val) > len(comments):
                    fm.c_format("$$eValue must be a whole number between 0 and " + str((len(comments))))
                    continue
                break
            if not val:
                break

            if int(val) == len(comments):
                new_comment = fm.c_input("Enter Comment: ").strip()
                if new_comment:
                    comments.append(new_comment)
            else:
                comments[int(val)] = fm.c_input("Edit Comment: ").strip()
        ratings.append([am.current_id, '0', r] + comments)
        dm.update_attribute('ratings', ratings, orders_list[int(book)])
        fm.c_format("$$gRating Published Successfully")
        return
    # editing already existing entry
    rating = ratings[ind]
    while True:
        fm.c_format("$$[ rated by $$$\n\t$$c$$i{}$$$\n"
                    "{}"
                    "$$[ rating $$$\n\t{}{:.2f}/10$$$\n"
                    "$$[ comments $$$".format(
                        dm.retrieve_user(rating[0])['username'] if dm.retrieve_user(rating[0]) is not None else
                        "$$$$$r$$~unknown",
                        "$$[ last edited by $$$\n\t$$i{}$$$\n".format(
                            ("$$c" + dm.retrieve_user(rating[1])['username']) if dm.retrieve_user(rating[1]) is not None else
                            ("$$y" + dm.retrieve_admin(rating[1])['username']) if dm.retrieve_admin(rating[1]) is not None else
                            "$$$$$r$$~unknown") if rating[1] != '0' else '',
                        "$$r" if float(rating[2]) < 3 else "$$y" if float(rating[2]) < 7 else "$$g",
                        float(rating[2])
                    ))
        for i, c in enumerate(rating[3:]):
            fm.c_format("\t[{}] - $$i{}$$$".format(i, c))
        # selecting category
        fm.c_format("Select one of the categories from the above to alter.")
        while True:
            category = fm.c_input("$$r[*]$$$Category $$i(Leave blank to finish editing)$$$: ")
            if category in ['rating', 'comments']:
                break
            if category in ['rated by', 'last edited by']:
                fm.c_format("$$EImmutable Category. Please enter a category again.")
                continue
            if not category:
                fm.c_format("$$F$$b$$iExiting Rate_Book function")
                return
            fm.c_format("$$eInvalid Category. Please enter a category again.")

        if category == 'comments':
            while True:
                fm.c_format("$$[ comments $$$")
                for i, c in enumerate(rating[3:]):
                    fm.c_format("\t[{}] - $$i{}$$$".format(i, c))
                fm.c_format("\t[{}] - ".format(len(rating) - 3))

                fm.c_format("Enter the index of the comment you want to edit $$i(leave blank to go back)$$$")
                while True:
                    val = fm.c_input("Index: ")
                    if not val:
                        break
                    if not is_int(val):
                        fm.c_format("$$eValue must be a whole number between 0 and " + str((len(rating) - 3)))
                        continue
                    if int(val) < 0 or int(val) > len(rating) - 3:
                        fm.c_format("$$eValue must be a whole number between 0 and " + str((len(rating) - 3)))
                        continue
                    break
                if not val:
                    break

                fm.c_format("Editing comment: $$i{}".format(rating[3 + int(val)] if int(val) < len(rating) - 3 else ""))
                comment = fm.c_input("New comment: ").strip()

                if int(val) == len(rating) - 3:
                    if comment:
                        rating.append(comment)
                else:
                    if comment:
                        rating[3 + int(val)] = comment
                    else:
                        del rating[3 + int(val)]

                rating[1] = am.current_id
                ratings[ind] = rating
                dm.update_attribute('ratings', ratings, orders_list[int(book)])
                fm.c_format("$$gUpdate Successful$$$")

        else:
            fm.c_format("Editing Rating: $$[{} {:.2f}/10 $$$".format(
                "$$r" if float(rating[2]) < 3 else "$$y" if float(rating[2]) < 7 else "$$g",
                float(rating[2]))
            )
            while True:
                val = fm.c_input("Enter new rating (leave blank to go back): ")
                if not val:
                    break
                if not is_float(val):
                    fm.c_format("$$eRating must be a number between 0 and 10)")
                    continue
                if float(val) < 0 or float(val) > 10:
                    fm.c_format("$$eRating must be between 0 and 10")
                    continue
                break
            if not val:
                continue

            rating[1] = am.current_id
            rating[2] = val
            ratings[ind] = rating
            dm.update_attribute('ratings', ratings, orders_list[int(book)])
            fm.c_format("$$gUpdate Successful$$$")


def view_ratings(book=-1):
    if am.current_id is None:
        fm.c_format("$$eNo user logged in. Please log in first.")
        return

    while book < 0:
        book = fm.c_input("Enter the id / title of the book you want to view ratings for $$i(leave blank to go back)$$$: ")
        if not book:
            return
        if dm.retrieve_book(book) is None:
            fm.c_format("$$eBook was not found in the system. Please enter a new value.")
            book = -1
            continue
        break
    ratings = dm.retrieve_book(book)['ratings']
    title = dm.retrieve_book(book)['title']
    while True:
        fm.c_format("$$i$$gViewing the ratings of $$i'$$p{}$$g'$$s with a rating of $$i$$[{}/10 $$$"
                    .format(title, dm.get_overall_rating(title)))
        for i, rating in enumerate(ratings):
            dm.print_formatted_rating(rating, "\t[{}] - ".format(i), True)
        fm.c_format("Enter the index of the rating you want to expand or leave blank to go back")
        while True:
            ind = fm.c_input("Index: ")
            if not ind:
                return
            if not is_int(ind):
                fm.c_format("$$eIndex must be a whole number between 0 and {}".format(len(ratings)-1))
                continue
            if int(ind) < 0 or int(ind) >= len(ratings):
                fm.c_format("$$eIndex must be a whole number between 0 and {}".format(len(ratings) - 1))
                continue
            break
        dm.print_formatted_rating(ratings[int(ind)], "")
        if am.is_admin:
            cmd = fm.c_input("$$gPress any key to continue $$i(Available commands: $$c{k}edit$$g, $$c{k}delete$$g)$$$$$i "
                             .format(k=command_key))
            if cmd == command_key + 'edit':
                edit_book(title)
            if cmd == command_key + 'delete':
                if not [v for v in am.current_user['bookstores'] if v in dm.retrieve_book(book)['bookstores']]:
                    fm.c_format("$$eYou do not have access to any of the libraries this book is housed in")
                else:
                    del ratings[int(ind)]
            continue
        fm.c_input("$$C$$0$$iWaiting for user input...")


def change_command_key():
    key = fm.c_input("Enter the new command suffix or leave blank to go back: ")
    if not key:
        return
    __calculate_commands(key)


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


def _is_admin():
    if am.current_id is None:
        fm.c_format("$$eNo used logged in. Please log in first.")
        return False
    if not am.is_admin:
        fm.c_format("$$eFunction available only to admins.")
        return False
    return True


def _is_user():
    if am.current_id is None:
        fm.c_format("$$eNo used logged in. Please log in first.")
        return False
    if am.is_admin:
        fm.c_format("$$eFunction available only to users.")
        return False
    return True


__calculate_commands(command_key)
