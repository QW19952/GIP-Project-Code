import csv
from datetime import datetime
import os
import json

class CSVWriter:
    def __init__(self, headers=None, folder_path="/home/gip-pi/Documents/TestData"):
        self.headers = headers
        self.folder_path = folder_path
        self.filepath = self.generate_filepath()
        self.headers_written = False  # Track if headers have been written

    def generate_filepath(self):
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"data_{current_datetime}.csv"
        return os.path.join(self.folder_path, filename)

    def write_data(self, data, new_headers=None):
        with open(self.filepath, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if new_headers:
                writer.writerow(new_headers)
            if not self.headers_written and self.headers:
                writer.writerow(self.headers)
                self.headers_written = True
            writer.writerows(data)
        #print(f"Data has been written to {self.filepath}")
        
    def generate_data_headers(self,count):
        headers = [f"V{i}" for i in range(1, count + 1)] #V 1-4
        headers += [f"I{i}" for i in range(1, count + 1)] #I 1-4
        headers += [f"T{i}" for i in range(1, count + 1)] #T 1-4
        headers += [f"Time"] #Time (s)
        return headers
        
    def generate_headers(self, inputs):
        default_headers = ["No. Battries", "Timestep", "Safety Temp.", "Test Duration", "Start Time"]
        test_headers = self.generate_data_headers(inputs[0])  # Assuming data[0] represents the count
        headers = [default_headers, inputs, test_headers]
        return headers
        
    def generate_json(self, count, data_list):
        headers = self.generate_data_headers(count)
        # Convert the list of rows into a list of dictionaries with headers as keys
        data = []
        for row in data_list:
            data.append({header: value for header, value in zip(headers, row)})
        Json = json.dumps(data, indent=4)
        return Json

# Example usage:
if __name__ == "__main__":
    # Sample initial data
    initial_data = [
        ['Name', 'Age', 'City'],
        ['John', 30, 'New York'],
        ['Alice', 25, 'Los Angeles'],
        ['Bob', 35, 'Chicago']
    ]
    
    # Sample test data with new headers
    test_data = [
        ['ID', 'Score'],
        ['1', 85],
        ['2', 90],
        ['3', 78]
    ]

    # Instantiate CSVWriter with initial data
    csv_writer = CSVWriter(headers=initial_data[0])

    # Write initial data to CSV file
    csv_writer.write_data(initial_data[1:])

    # Write more test data to CSV file without repeating headers
    csv_writer.write_data(test_data[1:])

    # Write additional data with new headers
    new_headers = ['Date', 'Amount']
    additional_data = [
        ['2024-03-15', 100],
        ['2024-03-16', 150],
        ['2024-03-17', 200]
    ]
    csv_writer.write_data(additional_data, new_headers=new_headers)
    
    h = csv_writer.generate_headers()
    csv_writer.write_data(h)
