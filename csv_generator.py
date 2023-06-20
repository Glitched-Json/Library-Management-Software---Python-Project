import pandas as pd
import random
from random import randint
from math import sqrt

usernames = list(pd.read_csv('datasets/usernames.csv', sep='\t', header=None).sample(frac=1).astype(str).values)
print("loaded file: 'datasets/usernames.csv'")
passwords = list(pd.read_csv('datasets/passwords.csv', sep='\t', header=None).sample(frac=1).astype(str).values)
print("loaded file: 'datasets/passwords.csv'")
addresses = pd.read_csv('datasets/addresses.csv').sample(frac=1).astype(str)
print("loaded file: 'datasets/addresses.csv'")
books = pd.read_csv('datasets/books-limited.csv', sep=';', dtype=str, header=1).sample(frac=1)
print("loaded file: 'datasets/books-limited.csv'")
genres = pd.read_csv('datasets/genres.csv', header=None).sample(frac=1)
print("loaded file: 'datasets/genres.csv'")
libraries = pd.read_csv('datasets/libraries.csv', header=None).sample(frac=1)
print("loaded file: 'datasets/libraries.csv'")
ratings = pd.read_csv('datasets/ratings-limited.csv').sample(frac=1)  # Books_rating
print("loaded file: 'datasets/ratings-limited.csv'")
ids_generated = []
user_ids_generated = []
admin_ids_generated = []
book_ids_generated = []
usernames_generated = []
book_titles_generated = []
authors_generated = []
publishers_generated = []
commenter = []
edited_by = []
ratings_score = ["{:.2f}".format(min(10., float(x) * 2 + random.random() * 2)) for x in ratings['review/score']]
ratings_review = ratings['review/summary']
ratings_comment = ratings['review/text']
ratings = [[ratings_score[x], ratings_review[x], ratings_comment[x]] for x in range(len(ratings_score))]
size = len(ratings)
# ratings['review/score'], ratings['review/summary'], ratings['review/text']


def random_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)


def get_valid_id(n):
    new_id = random_n_digits(n)
    tries = 100
    while new_id in ids_generated:
        new_id = random_n_digits(n)
        tries -= 1
        if tries == 0:
            tries = 100
            n += 1
    ids_generated.append(new_id)
    return new_id


def get_valid_username():
    tries = 100
    username = random.choice(usernames)[0]
    while username in usernames_generated and tries > 0:
        username = random.choice(usernames)[0]
        tries -= 1
    if username in usernames_generated:
        return None
    usernames_generated.append(username)
    return username


def generate_users(n, file='resources/users.csv', listed=False, sanity_check=-1):
    df = pd.DataFrame(
        columns=['id', 'username', 'password', 'address', 'city', 'orders', 'favorites', 'balance']).astype(object)
    global ids_generated, usernames_generated
    ids_generated = ids_generated.copy()
    usernames_generated = usernames_generated.copy()
    generated = 0
    for x in range(n):
        if sanity_check > 0 and generated % sanity_check == 0:
            print("generating users: currently at [" + str(generated) + "]")
        # get username
        name = get_valid_username()
        if name is None:
            continue

        # get address
        ad = addresses.sample()

        # get list of ordered books
        n_orders = min(random.randint(0, 40), len(book_ids_generated))
        orders = []
        if n_orders > 0:
            orders = random.sample(book_ids_generated, n_orders)

        # get list of favorite books
        n_favorites = min(random.randint(0, 8), len(book_ids_generated))
        favorites = []
        if n_favorites > 0:
            favorites = random.sample(book_ids_generated, n_favorites)
            favorites = [x for x in favorites if x not in orders]
        # generate user dict
        user = dict(
            id=user_ids_generated[generated] if listed else str(get_valid_id(8)),
            username=name,
            password=str(hash(random.choice(passwords)[0])),
            address=ad['address'].to_string(index=False),
            city=ad['city'].to_string(index=False),
            orders=orders,
            favorites=favorites,
            balance=random.randint(500, 1500) / 10
        )
        # append generated user to the list
        df.loc[len(df.index)] = user
        generated += 1
    # store generated list to the file specified
    df.to_csv(file, index=False)
    print("Generated " + str(generated) + " valid user entries")


def generate_admins(n, file='resources/admins.csv', listed=False, sanity_check=-1):
    df = pd.DataFrame(columns=['id', 'username', 'password', 'bookstores']).astype(object)
    global ids_generated, usernames_generated
    ids_generated = ids_generated.copy()
    usernames_generated = usernames_generated.copy()
    generated = 0
    for x in range(n):
        if sanity_check > 0 and generated % sanity_check == 0:
            print("generating admins: currently at [" + str(generated) + "]")
        # get username
        name = get_valid_username()
        if name is None:
            continue
        # generate admin dict
        admin = dict(
            id=admin_ids_generated[generated] if listed else str(get_valid_id(6)),
            username=get_valid_username(),
            password=str(hash(random.choice(passwords)[0])),
            bookstores=libraries.sample(random.randint(1, 15))[0].tolist()
        )
        # append generated admin to the list
        df.loc[len(df.index)] = admin
        generated += 1
    # store generated list to the specified file
    df.to_csv(file, index=False)
    print("Generated " + str(generated) + " valid admin entries")


def generate_books(n, file='resources/books.csv', listed=False, sanity_check=-1):
    df = pd.DataFrame(
        columns=['id', 'title', 'author', 'publisher', 'categories', 'cost', 'availability', 'copies', 'bookstores',
                 'ratings']).astype(object)
    global ids_generated, usernames_generated
    j = 0
    ids_generated = ids_generated.copy()
    usernames_generated = usernames_generated.copy()
    generated = 0
    for x in range(n):
        if sanity_check > 0 and generated % sanity_check == 0:
            print("generating books: currently at [" + str(generated) + "]")
        # generate book
        if not listed:
            tries = 100
            bk = books.sample().astype(str).to_dict("records")
            while (bk[0].get('ISBN') in ids_generated or bk[0].get('Book-Title') in usernames_generated) and tries > 0:
                bk = books.sample().astype(str).to_dict("records")
                tries -= 1
            if tries == 0:
                continue
            # append fetched book's id and title to the database
            ids_generated.append(bk[0].get('ISBN'))
            book_titles_generated.append(bk[0].get('Book-Title'))
        # generate bookstore availability and storing
        n_stores = random.randint(1, 10)
        stores = libraries.sample(n_stores)[0].tolist()
        # generate random ratings
        rating: list[list[str]] = []
        for i in range(random.randint(3, 10)):
            if not listed:
                user_id = random.choice(user_ids_generated)
                admin_id = '0'
                if random.random() < 0.2:
                    admin_id = random.choice(admin_ids_generated)
                r = random.choice(ratings)
                rating.append(
                    [user_id, admin_id, r[0], r[1], r[2]])
            else:
                rating.append([commenter[j]] + [edited_by[j]] + ratings[j])
                j = (j + 1) % size
        # generate book dict
        book = dict(
            id=book_ids_generated[generated] if listed else bk[0].get('ISBN'),
            title=book_titles_generated[generated] if listed else bk[0].get('Book-Title'),
            author=authors_generated[generated] if listed else bk[0].get('Book-Author'),
            publisher=publishers_generated[generated] if listed else bk[0].get('Publisher'),
            categories=genres.sample(min(random.randint(1, 6), random.randint(1, 6)))[0].tolist(),
            cost=max(2.49, int(random.gauss(22, 9))) + random.choice([0, 0.49, 0.49, 0.5, 0.99, 0.99]),
            availability=random.choices(stores, k=random.randint(int(sqrt(n_stores)) - 1, n_stores)),
            copies=random.randint(5, 100),
            bookstores=stores,
            ratings=rating
        )
        # append generated book to the list
        df.loc[len(df.index)] = book
        generated += 1
    # store generated list of books to the specified file
    df.to_csv(file, index=False)
    print("Generated " + str(generated) + " valid book entries")


def generate_all(users, admins, book_n, files, sanity_check=-1):
    u = 0
    a = 0
    b = 0
    for i in range(users):
        if sanity_check > 0 and i % sanity_check == 0:
            print("at " + str(i) + " prepared users")
        user_ids_generated.append(str(get_valid_id(8)))
        ids_generated.append(user_ids_generated[-1])
        u += 1
    print("prepared " + str(u) + " user ids")
    for i in range(admins):
        if sanity_check > 0 and i % sanity_check == 0:
            print("at " + str(i) + " prepared admins")
        admin_ids_generated.append(str(get_valid_id(6)))
        ids_generated.append(admin_ids_generated[-1])
        a += 1
    print("prepared " + str(a) + " admin ids")
    for i in range(book_n):
        if sanity_check > 0 and i % sanity_check == 0:
            print("at " + str(i) + " prepared books")
        bk = books.iloc[i]
        book_ids_generated.append(bk.get('ISBN'))
        book_titles_generated.append(bk.get('Book-Title'))
        authors_generated.append(bk.get("Book-Author"))
        publishers_generated.append(bk.get("Publisher"))
        ids_generated.append(book_ids_generated[-1])
        b += 1
    for i in range(size):
        if sanity_check > 0 and i % sanity_check == 0:
            print("at " + str(i) + " prepared ratings")
        commenter.append(user_ids_generated[i % len(user_ids_generated)])
        edited_by.append(admin_ids_generated[i % len(admin_ids_generated)] if random.random() < 0.2 else '0')
    print("prepared " + str(b) + " book ids, titles, authors and publishers")
    generate_users(u, files[0], True, sanity_check)
    generate_admins(a, files[1], True, sanity_check)
    generate_books(b, files[2], True, sanity_check)
