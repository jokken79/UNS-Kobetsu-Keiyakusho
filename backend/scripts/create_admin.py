#!/usr/bin/env python3
"""
Create Admin User Script

Creates an initial admin user for the UNS Kobetsu Keiyakusho system.
Run this script after database initialization.

Usage:
    python scripts/create_admin.py
    python scripts/create_admin.py --email admin@company.com --password securepass123
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash


def create_admin_user(email: str, password: str, full_name: str = "Admin User"):
    """
    Create an admin user in the database.

    In a full implementation, this would insert into a Users table.
    For now, it prints the hashed password for manual configuration.
    """
    # Hash the password
    hashed_password = get_password_hash(password)

    print("\n" + "=" * 60)
    print("Admin User Created")
    print("=" * 60)
    print(f"Email: {email}")
    print(f"Full Name: {full_name}")
    print(f"Role: admin")
    print(f"Password Hash: {hashed_password}")
    print("=" * 60)

    # In a full implementation, insert into database:
    # db = SessionLocal()
    # try:
    #     from app.models.user import User
    #     user = User(
    #         email=email,
    #         hashed_password=hashed_password,
    #         full_name=full_name,
    #         role="admin",
    #         is_active=True,
    #     )
    #     db.add(user)
    #     db.commit()
    #     print(f"User {email} created successfully!")
    # except Exception as e:
    #     print(f"Error creating user: {e}")
    #     db.rollback()
    # finally:
    #     db.close()

    print("\nTo use this admin user, add to the _demo_users dict in auth.py:")
    print(f'''
    "{email}": {{
        "id": 1,
        "email": "{email}",
        "full_name": "{full_name}",
        "hashed_password": "{hashed_password}",
        "role": "admin",
        "is_active": True,
    }}
    ''')

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Create an admin user for UNS Kobetsu Keiyakusho"
    )
    parser.add_argument(
        "--email",
        type=str,
        default="admin@example.com",
        help="Admin email address"
    )
    parser.add_argument(
        "--password",
        type=str,
        default="admin123",
        help="Admin password (min 8 characters)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default="System Administrator",
        help="Admin full name"
    )

    args = parser.parse_args()

    # Validate password
    if len(args.password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)

    # Create admin
    success = create_admin_user(
        email=args.email,
        password=args.password,
        full_name=args.name
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
