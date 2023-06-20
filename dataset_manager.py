import pandas as pd
import account_manager as am
import format_manager as fm
from ast import literal_eval
from typing import Optional
from random import randint

"""
Structure of compressed categories:
    bookstores: ['LibraryName1', 'LibraryName2', ...]
    orders: [BookID1, BookID2, ...]
    favorites: [BookID1, BookID2, ...]
    availability: [LibraryName1, LibraryName2, ...]
    categories: [CategoryName1, CategoryName2, ...]
    ratings: [[UserID, Last Edited by ID, Rating (float), comment1, comment2, ...], ...]
"""
compressed_keys = ["bookstores", "orders", "favorites", "availability", "categories", "ratings"]
books = pd.DataFrame(
    columns=['id', 'title', 'author', 'publisher', 'categories', 'cost', 'availability', 'copies', 'bookstores',
             'ratings'])
users = pd.DataFrame(columns=['id', 'username', 'password', 'address', 'city', 'orders', 'favorites', 'balance'])
admins = pd.DataFrame(columns=['id', 'username', 'password', 'bookstores'])
ids = []
book_ids = []
usernames = []
titles = []
imported = 0
resource_files = []


def delete_entry(entry_id):
    global users, admins, books
    entry = retrieve_user(entry_id)
    if entry is None:
        entry = retrieve_admin(entry_id)
        if entry is None:
            entry = retrieve_book(entry_id)
            if entry is None:
                fm.c_format("$$eDid not find entry with id $$$$$E'{}'$$$".format(entry_id))
            # id found in books
            books = books[books.id != entry_id]
            fm.c_format("$$gDeleted book with id $$p$$i'{}'$$$".format(entry_id))
            return
        # id found in admins
        admins = admins[admins.id != entry_id]
        fm.c_format("$$gDeleted admin with id $$y$$i'{}'".format(entry_id))
        return
    # id found in users
    users = users[users.id != entry_id]
    fm.c_format("$$gDeleted user with id $$c$$i'{}'".format(entry_id))


def check_username_validity(username, data=None):
    if data is None:
        data = usernames
    return username not in data


def retrieve_user(x: Optional[str]):
    if x is None:
        return None
    if x in users['username'].values:
        u = users.loc[users['username'] == x]
        if not u.empty:
            return u.to_dict('records')[0]
        return None
    if x in users['id'].values:
        u = users.loc[users['id'] == x]
        if not u.empty:
            return u.to_dict('records')[0]
        return None
    return None


def retrieve_admin(x: Optional[str]):
    if x is None:
        return None
    if x in admins['username'].values:
        a = admins.loc[admins['username'] == x]
        if not a.empty:
            return a.to_dict('records')[0]
        return None
    if x in admins['id'].values:
        a = admins.loc[admins['id'] == str(x)]
        if not a.empty:
            return a.to_dict('records')[0]
    return None


def retrieve_book(x: Optional[str]):
    if x is None:
        return None
    if x in titles:
        b = books.loc[books['title'] == x]
        if not b.empty:
            return b.to_dict('records')[0]
        return None
    if x in book_ids:
        b = books.loc[books['id'] == x]
        if not b.empty:
            return b.to_dict('records')[0]
    return None


def update_attribute(category, value, entry_id=None):
    if entry_id is None:
        entry_id = am.current_id
    if entry_id is None:
        return
    if entry_id in book_ids:
        if category in books.columns:
            books.at[books.index[books['id'] == entry_id].tolist()[0], category] = value
        return
    if am.is_admin:
        if am.current_id in admins['id'].values and category in admins.columns:
            admins.at[admins.index[admins['id'] == am.current_id].tolist()[0], category] = value
        return
    if am.current_id in users['id'].values and category in users.columns:
        users.at[users.index[users['id'] == am.current_id].tolist()[0], category] = value


def import_users(file, output=True):
    global imported
    imported_users = pd.read_csv(
        file,
        keep_default_na=False,
        converters={"id": str, "username": str, "password": str, "address": str, "city": str, "orders": c_literal,
                    "favorites": c_literal, "balance": float}).to_dict('records')
    imported = 0
    [import_user(user) for user in imported_users if user['id'] not in ids and user['username'] not in usernames]
    if output:
        print("Imported " + str(imported) + " users from file '" + file + "'")


def import_admins(file, output=True):
    global imported
    imported_admins = pd.read_csv(
        file,
        keep_default_na=False,
        converters={"id": str, "username": str, "password": str, "bookstores": c_literal}).to_dict('records')
    imported = 0
    [import_admin(admin) for admin in imported_admins if admin['id'] not in ids and admin['username'] not in usernames]
    if output:
        print("Imported " + str(imported) + " admins from file '" + file + "'")


def import_books(file, output=True):
    global imported
    imported_books = pd.read_csv(
        file,
        keep_default_na=False,
        converters={"id": str, "title": str, "author": str, "publisher": str, "categories": c_literal,
                    "cost": float, "availability": c_literal, "copies": int, "bookstores": c_literal,
                    "ratings": c_literal}).to_dict('records')
    imported = 0
    [import_book(book) for book in imported_books if book['id'] not in ids and book['title'] not in titles]
    if output:
        print("Imported " + str(imported) + " books from file '" + file + "'")


def import_user(user):
    global imported
    imported += 1
    users.loc[len(users.index)] = user
    usernames.append(user['username'])
    ids.append(user['id'])


def import_admin(admin):
    global imported
    imported += 1
    admins.loc[len(admins.index)] = admin
    usernames.append(admin['username'])
    ids.append(admin['id'])


def import_book(book):
    global imported
    imported += 1
    books.loc[len(books.index)] = book
    titles.append(book['title'])
    ids.append(book['id'])
    book_ids.append(book['id'])


def print_formatted(x: dict, max_n=-1):
    for k in x:
        fm.c_format("$$i$$[ " + k + ": $$${}".format(
            " - overall rating $$i$$[ {} $$$".format(x['id']) if k == 'ratings' else ''
        ))
        if k in compressed_keys:
            if k == "ratings":
                for i, v in enumerate(x[k]):
                    if i == max_n:
                        fm.c_format("\t...")
                        break
                    print_formatted_rating(v, "\t", True, True)
                continue
            values = x[k]
            if k == "orders" or k == "favorites":
                values = map(lambda b: "\t[" + b + "]" if retrieve_book(b) is None else "\t[{}] - $$i$$[{} $$$ - {}"
                             .format(
                                retrieve_book(b)['id'],
                                get_overall_rating(retrieve_book(b)['id']),
                                retrieve_book(b)['title']),
                             values)
            for i, v in enumerate(values):
                if i == max_n:
                    fm.c_format("\t...")
                    break
                fm.c_format(v)
            continue
        fm.c_format("\t$$i" + (str(x[k]) if k != "password" else "********"))


def print_formatted_rating(rating, suffix="", compressed=False, numbered=False) -> list[str]:
    fm.c_format("{}$$[{} {:.2f}/10 $$$ - by $$c$$i{} {}$$${}".format(
        suffix,
        "$$r" if float(rating[2]) < 3 else "$$y" if float(rating[2]) < 7 else "$$g",
        float(rating[2]),
        retrieve_user(str(rating[0]))['username'] if retrieve_user(str(rating[0])) is not None else "$$$$$r$$~unknown",
        "" if rating[1] == '0' else ("$$$- last edited by {} ".format(
            "$$c$$i" + retrieve_user(str(rating[1]))['username'] if retrieve_user(str(rating[1])) is not None else
            "$$y$$i" + retrieve_admin(str(rating[1]))['username'] if retrieve_admin(str(rating[1])) is not None else
            "$$$$$r$$~unknown"
        )),
        "..." if compressed else ""
    ))
    if compressed:
        return rating[3:]
    if numbered:
        for i, c in enumerate(rating[3:]):
            fm.c_format("{}\t[{}] - $$i{}$$$".format(suffix, i, c))
        return rating[3:]
    for c in rating[3:]:
        fm.c_format("{}\t$$*\u2022 $$$$$i{}$$$".format(suffix, c))
    return rating[3:]


def get_overall_rating(book):
    book = retrieve_book(book)
    if book is None:
        return '$$r$$~unknown$$$'
    ratings = book['ratings']
    if len(ratings) == 0:
        return 'unrated'
    score = 0
    for rating in ratings:
        score += float(rating[2])
    score = score / len(ratings)
    return "{} {:.2f}".format("$$r" if score < 3 else "$$y" if score < 7 else "$$g", score)


def __save_dataframes(resources=None):
    if resources is None:
        resources = resource_files
    users.to_csv(resources[0], index=False)
    admins.to_csv(resources[1], index=False)
    books.to_csv(resources[2], index=False)


def __load_all(resources):
    global resource_files
    resource_files = resources
    import_users(resources[0], False)
    import_admins(resources[1], False)
    import_books(resources[2], False)


def c_literal(x):
    try:
        return literal_eval(x)
    except ValueError:
        fm.c_format("$$EError Value: {}".format(x))
        return []


def get_valid_id(n, tries=100):
    new_id = random_n_digits(n)
    while new_id in ids:
        new_id = random_n_digits(n)
        tries -= 1
        if tries == 0:
            tries = 100
            n += 1
    return new_id


def random_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)
