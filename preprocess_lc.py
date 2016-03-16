#!python3
import argparse
import sqlite3
import os
import csv

DATA_DELIMITER = ","
LINES_TO_SKIP = 1 # Any meta-data we want to skip over

NORMALIZE = "normalize"
CATEGORIZE = "categorize"
NOTHING = "nothing"

# column_name => NORMALIZE|CATEGORIZE
data_configuration = {
    "loan_amnt": NORMALIZE,
    "funded_amnt_inv": NORMALIZE,
    "term": CATEGORIZE,
    "int_rate": NORMALIZE,
    "installment": NORMALIZE,
    "emp_length": CATEGORIZE,
    "home_ownership": CATEGORIZE,
    "annual_inc": NORMALIZE,
    "verification_status": CATEGORIZE,
    "purpose": CATEGORIZE,
    "dti": NORMALIZE,
    "grade": NOTHING
    }

def main():
    """
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", type=str, help="Path to CSV file")
    parser.add_argument("--svm", action="store_true", help="output svm file?")
    args = parser.parse_args()
    
    if(not os.path.exists(args.csv_file)):
        print("Could not find CSV file directory")
        exit(1)
        
    # Read column data from CSV file
    column_table, row_number = parse_csv_file(args.csv_file)
    
    #for key, column in column_table.items():
    #    print(key, len(column), column[-1])
    
    # Process the columns we want
    output_columns = {}
    for column_name,method in data_configuration.items():
        if(column_table.get(column_name) is not None):
            if(method == NORMALIZE):
                try:
                    output_columns[column_name] = normalize_column(column_table[column_name])
                except Exception as e:
                    print("Error on column", column_name, e)
            elif(method == CATEGORIZE):
                for new_name, new_column in categorize_column(column_table[column_name]).items():
                    output_columns[new_name] = new_column
            elif(method == NOTHING):
                output_columns[column_name] = column_table[column_name]
        else:
            print("Skipping column " + column_name)
    
    # Save processed data to a new file
    with open(args.csv_file + ".processed.csv", 'w', encoding="utf8") as f:
        column_idx = 0
        header_list = [] # Need to know order we are writing to file in, dicts are not ordered
        column_number = len(output_columns.keys())
        for column_name in output_columns.keys():
            header_list.append(column_name)
            f.write(column_name)
            column_idx += 1
            if(column_idx == column_number):
                f.write("\n")
            else:
                f.write(",")
                
        for row in range(row_number):
            column_idx = 0
            for header in header_list:
                f.write(str(output_columns[header][row]))
                column_idx += 1
                if(column_idx == column_number):
                    f.write("\n")
                else:
                    f.write(",")                
            

def normalize_column(column):
    """ Normalize column data on a scale of [0,1]
    """
    max_value = 0
    min_value = 0
    
    # Convert to floats
    for idx,value in enumerate(column):
        column[idx] = float(value.strip("% "))
    
    # Find max and min
    max_value = max(column)
    min_value = min(column)

    # Normalize each value
    # (value - min)/(max - min)
    for idx,value in enumerate(column):
        column[idx] = round((value - min_value)/(max_value - min_value),4)
        
        if(column[idx] > 1):
            print(value, max_value, min_value)
    
    return column

def categorize_column(column):
    """ Create new binary asymmetric columns from a single column with discrete values.
    """
    # Get set of unique values
    discrete_values = set()
    for value in column:
        discrete_values.add(value)
        
    # Create a column for each value
    new_columns = {}
    for value in discrete_values:
        new_columns[value] = []
        
    # Assign 0/1 based on value and column
    for discrete_value in discrete_values:
        for value in column:
            if(value == discrete_value):
                new_columns[discrete_value].append(1)
            else:
                new_columns[discrete_value].append(0)

    return new_columns

def format_for_libsvm():
    #Turn sql data into lib svm format
    #lib svm format: <label> <feature_idx>:<feature_value> <feature_idx>:<feature_value> ...
    #also scale any non-binary data from 0 to 1.
    return

def parse_csv_file(csv_file):
    """
    """
    print("Loading " + csv_file)
    header_index_table = {}
    column_table = {}
    
    # Count the number of lines
    line_number = 0
    with open(csv_file, 'r', encoding="utf8") as f:
        for line in f:
            line_number += 1
    
    # Read each line into memory
    line_count = 0
    row_number = 0
    with open(csv_file, 'r', encoding="utf8") as f:
        reader = csv.reader(f)
        for data_line in reader:
            if(line_count > LINES_TO_SKIP):
                if(not check_line(data_line, header_index_table)): continue
                row_number +=  1
                for idx, data in enumerate(data_line):
                    data = data.strip("\"'")
                    column_table[header_index_table[idx]].append(data)
            elif(line_count == LINES_TO_SKIP):
                for idx, header in enumerate(data_line):
                    header = header.strip("\"'")
                    header_index_table[idx] = header
                    column_table[header] = []
                    
            line_count += 1
            
            if(line_count % 10000 == 0):
                print(round(float(line_count/line_number)*100,2), "% complete")
                
    print("Done loading " + csv_file)
    
    return (column_table, row_number)

def check_line(data_line, header_index_table):
    """ Validate that all columns we want exist in sample
    """
    if(len(data_line) < 2): return False
    for idx, data in enumerate(data_line):  
        data = data.strip("\"'")  
        if(data == "" and header_index_table[idx] in data_configuration.keys()): return False
    return True
    
if __name__ == "__main__": main()