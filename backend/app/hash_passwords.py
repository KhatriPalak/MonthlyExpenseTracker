import bcrypt

# Plain text passwords
passwords = ['password123', 'securepass']

for pwd in passwords:
    hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
    print(f"Plain: {pwd}\nHashed: {hashed.decode()}\n")
