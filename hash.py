import bcrypt

def generate_hashed_password(password):
    # Generate a salt
    salt = bcrypt.gensalt()
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Example usage
if __name__ == "__main__":
    plain_password = input("Enter the password to hash: ")
    hashed_password = generate_hashed_password(plain_password)
    print(f"Hashed Password: {hashed_password}")
