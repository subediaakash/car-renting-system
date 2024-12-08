import datetime
from typing import List, Dict, Optional


class FileReader:
    
    @staticmethod
    def read_file(filename: str, parser: callable) -> List[Dict]:
    
        try:
            with open(filename, "r") as f:
                return [parser(line.strip()) for line in f]
        except FileNotFoundError:
            print(f"File {filename} not found.")
            return []


class VehicleRentalSystem:
    
    def __init__(self):
        self.vehicle_parser = lambda line: dict(zip(
            ['reg', 'model', 'rate', 'properties'], 
            [line.split(',')[0], line.split(',')[1], float(line.split(',')[2]), line.split(',')[3:]]
        ))
        
        self.customer_parser = lambda line: dict(zip(
            ['dob', 'fname', 'lname', 'email'], 
            line.split(',')
        ))
        
        self.rented_parser = lambda line: dict(zip(
            ['reg', 'customer_dob', 'start_time'], 
            line.split(',')
        ))
        
        self.transaction_parser = lambda line: dict(zip(
            ['reg', 'dob', 'start', 'end', 'days', 'price'], 
            [*line.split(',')[:4], int(line.split(',')[4]), float(line.split(',')[5])]
        ))

    def read_vehicles(self) -> List[Dict]:
        return FileReader.read_file("vehicles.txt", self.vehicle_parser)

    def read_customers(self) -> List[Dict]:
        return FileReader.read_file("customers.txt", self.customer_parser)

    def read_rented(self) -> List[Dict]:
        return FileReader.read_file("rentedVehicles.txt", self.rented_parser)

    def read_transactions(self) -> List[Dict]:
        return FileReader.read_file("transActions.txt", self.transaction_parser)

    def list_available_cars(self) -> None:
        vehicles = self.read_vehicles()
        rented_regs = {r['reg'] for r in self.read_rented()}
        
        available_cars = [car for car in vehicles if car['reg'] not in rented_regs]
        
        if not available_cars:
            print("\nNo cars are currently available.")
            return

        print("\nAvailable cars:")
        for car in available_cars:
            print(f"*Reg. nr. {car['reg']}, Model: {car['model']}, "
                  f"Price per day: {car['rate']} ")
            print(f"Properties: {', '.join(car['properties'])}")

    def validate_customer(self, dob: str) -> bool:
       
        try:
            birth_date = datetime.datetime.strptime(dob, "%d/%m/%Y")
            age = datetime.datetime.now().year - birth_date.year
            
            if not (18 <= age <= 75):
                print("Customer should be between 18 and 75 years old to rent a car.")
                return False
            
            customers = self.read_customers()
            if any(c['dob'] == dob for c in customers):
                print("Customer details already exists.")
                return False
            
            return True
        
        except ValueError:
            print("Invalid date format. Please use DD/MM/YYYY")
            return False

    def add_customer(self) -> Optional[str]:
      
        print("\nEnter customer details:")
        while True:
            dob = input("Date of birth (DD/MM/YYYY): ")
            if not self.validate_customer(dob):
                return None

            fname = self._get_validated_name("First")
            lname = self._get_validated_name("Last")
            email = self._get_validated_email()

            with open("customers.txt", "a") as f:
                f.write(f"{dob},{fname},{lname},{email}\n")

            return dob

    @staticmethod
    def _get_validated_name(name_type: str) -> str:
      
        while True:
            name = input(f"{name_type} name: ").strip().upper()
            if not any(c.isdigit() for c in name):
                return name
            print("Name cannot contain numbers. Please try again.")

    @staticmethod
    def _get_validated_email() -> str:
  
        while True:
            email = input("Email: ").strip()
            if '@' in email and '.' in email and len(email) > 3:
                return email
            print("Invalid email format. Please enter a valid email address.")

    def rent_car(self) -> None:
        vehicles = self.read_vehicles()
        rented_regs = {r['reg'] for r in self.read_rented()}
        available = [v for v in vehicles if v['reg'] not in rented_regs]

        if not available:
            print("\nSorry, no cars are currently available.")
            return

        reg = self._select_available_car(available)
        if not reg:
            return

        dob = self.add_customer()
        if not dob:
            return

        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        with open("rentedVehicles.txt", "a") as f:
            f.write(f"{reg},{dob},{now}\n")

        print("\nCar rented successfully!")

    @staticmethod
    def _select_available_car(available_cars: List[Dict]) -> Optional[str]:
       
        while True:
            reg = input("\nEnter registration number of car to rent: ")
            if any(car['reg'] == reg for car in available_cars):
                return reg
            print("Invalid registration number. Please try again.")
            return None

    def return_car(self) -> None:
        reg = input("\nEnter registration number of car to return: ")

        rented = self.read_rented()
        rental = next((r for r in rented if r['reg'] == reg), None)

        if not rental:
            print("No rental found for this registration number.")
            return

        vehicles = self.read_vehicles()
        car = next(v for v in vehicles if v['reg'] == reg)

        start_time = datetime.datetime.strptime(rental['start_time'], "%d/%m/%Y %H:%M")
        end_time = datetime.datetime.now()

        days = (end_time - start_time).days + 1
        cost = days * car['rate']

        with open("transActions.txt", "a") as f:
            f.write(
                f"{reg},{rental['customer_dob']},{rental['start_time']},"
                f"{end_time.strftime('%d/%m/%Y %H:%M')},{days},{cost:.2f}\n"
            )

        with open("rentedVehicles.txt", "r") as f:
            lines = f.readlines()
        with open("rentedVehicles.txt", "w") as f:
            f.writelines(line for line in lines if not line.startswith(reg))

        print(f"\nCar returned successfully!")
        print(f"Rental duration: {days} days")
        print(f"Total cost: ${cost:.2f}")

    def count_money(self) -> None:
        transactions = self.read_transactions()
        if not transactions:
            print("\nNo completed rentals yet.")
            return

        total = sum(t['price'] for t in transactions)
        print(f"\nTotal earnings: ${total:.2f}")
        print(f"Number of completed rentals: {len(transactions)}")

    def run(self) -> None:
        menu_options = {
            "1": ("List available cars", self.list_available_cars),
            "2": ("Rent a car", self.rent_car),
            "3": ("Return a car", self.return_car),
            "4": ("Count money", self.count_money)
        }

        while True:
            print("\n=== Car Rental System ===")
            for key, (description, _) in menu_options.items():
                print(f"{key}. {description}")
            print("0. Exit")

            choice = input("\nWhat is your selection? ")

            if choice == "0":
                print("\nThank you for using the Car Rental System!")
                break

            action = menu_options.get(choice)
            if action:
                action[1]()
            else:
                print("\nInvalid selection. Please choose a valid option.")


def main():
    rental_system = VehicleRentalSystem()
    rental_system.run()


if __name__ == "__main__":
    main()