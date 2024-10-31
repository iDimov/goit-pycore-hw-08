import re
import pickle
from collections import UserDict
from typing import List, Optional
from datetime import datetime, timedelta


class Field:
    def __init__(self, value: str):
        self._validate(value)
        self.value = value

    def _validate(self, value: str):
        pass

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def _validate(self, value: str):
        if not re.match(r'^\d{10}$', value):
            raise ValueError("Phone number must have 10 digits.")


class Birthday(Field):
    def _validate(self, value: str):
        try:
            datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    @property
    def date(self) -> datetime:
        return datetime.strptime(self.value, "%d.%m.%Y")


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: List[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone: str, new_phone: str):
        for p in self.phones:
            if p.value == old_phone:
                p.value = Phone(new_phone).value
                return
        raise ValueError("Phone not found.")

    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)

    def get_birthday(self) -> str:
        return self.birthday.value if self.birthday else "Birthday not set."

    def days_to_birthday(self) -> Optional[int]:
        if self.birthday:
            today = datetime.today()
            next_birthday = self.birthday.date.replace(year=today.year)
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)
            return (next_birthday - today).days
        return None

    def __str__(self) -> str:
        phones = '; '.join(p.value for p in self.phones)
        birthday = self.get_birthday()
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name)

    def delete(self, name: str):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Contact not found.")

    def get_upcoming_birthdays(self) -> List[Record]:
        today = datetime.today()
        next_week = today + timedelta(days=7)
        return [
            record for record in self.data.values()
            if record.birthday and today <= record.birthday.date.replace(year=today.year) <= next_week
        ]

    def save_to_file(self, filename="addressbook.pkl"):
        with open(filename, "wb") as file:
            pickle.dump(self.data, file)

    def load_from_file(self, filename="addressbook.pkl"):
        try:
            with open(filename, "rb") as file:
                self.data = pickle.load(file)
        except FileNotFoundError:
            self.data = {}


# Decorator for handling input errors
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, KeyError, IndexError) as e:
            return str(e)
    return wrapper


@input_error
def add_contact(args: List[str], book: AddressBook) -> str:
    name, phone = args[0], args[1] if len(args) > 1 else None
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    else:
        message = "Contact updated."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def add_birthday(args: List[str], book: AddressBook) -> str:
    name, birthday = args[0], args[1]
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    record.add_birthday(birthday)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args: List[str], book: AddressBook) -> str:
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    return f"{name}'s birthday is {record.get_birthday()}"


@input_error
def birthdays(_: List[str], book: AddressBook) -> str:
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next week."
    return "\n".join(str(record) for record in upcoming)


def parse_input(user_input: str) -> (str, List[str]):
    parts = user_input.split()
    command = parts[0]
    args = parts[1:]
    return command, args


def main():
    book = AddressBook()
    # Load existing data when starting the program
    book.load_from_file()
    
    print("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            # Save data before exiting
            book.save_to_file()
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))
            # Save after adding a contact
            book.save_to_file()

        elif command == "change":
            name, old_phone, new_phone = args
            record = book.find(name)
            if record:
                print(record.edit_phone(old_phone, new_phone))
                # Save after changing a phone number
                book.save_to_file()
            else:
                print("Contact not found.")

        elif command == "phone":
            name = args[0]
            record = book.find(name)
            if record:
                print(f"{name}'s phones: {', '.join(p.value for p in record.phones)}")
            else:
                print("Contact not found.")

        elif command == "all":
            for record in book.data.values():
                print(record)

        elif command == "add-birthday":
            print(add_birthday(args, book))
            # Save after adding a birthday
            book.save_to_file()

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()