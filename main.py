import dataset_manager as dm
import commands_manager as cm

# 50.000 users, 1.000 admins, 100.000 books
full = ['resources/users.csv', 'resources/admins.csv', 'resources/books.csv']
# 1.000 users, 10 admins, 1.000 books
lite = ['resources/users-lite.csv', 'resources/admins-lite.csv', 'resources/books-lite.csv']
# 100 users, 10 admins, 500 books
minimal = ['resources/users-minimal.csv', 'resources/admins-minimal.csv', 'resources/books-minimal.csv']

dm.__load_all(lite)
cm.run_console()
dm.__save_dataframes()
