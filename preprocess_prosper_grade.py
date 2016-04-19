#!/usr/bin/env python
import argparse
import sqlite3
import os
import csv
import statistics

NORMALIZE = "normalize"
CATEGORIZE = "categorize"
NOTHING = "nothing"
ENUMERATE = "enumerate"

#######################################################
################ Configuration ########################
#######################################################
# Any meta-data we want to skip over; 
# how many rows until we get the header
LINES_TO_SKIP = 0

# column_name => NORMALIZE|CATEGORIZE|ENUMERATE|NOTHING
data_configuration = {
    "amount_funded": NORMALIZE,
    "listing_term": CATEGORIZE,
    "borrower_rate": NORMALIZE,
    "listing_monthly_payment": NORMALIZE,
    "prosper_rating": CATEGORIZE,
    "months_employed": NORMALIZE,
    "is_homeowner": CATEGORIZE,
    "stated_monthly_income": NORMALIZE,
    "income_verifiable": CATEGORIZE,
    "fico_low": NORMALIZE,
    "inquiries_last6_months": NORMALIZE,
    "employment_status_description": CATEGORIZE,
    "occupation": CATEGORIZE,
    "borrower_state": CATEGORIZE,
    "prior_prosper_loans": NORMALIZE,
    "monthly_debt": NORMALIZE,
    "current_delinquencies": NORMALIZE,
	"current_credit_lines": NORMALIZE,
	"bankcard_utilization": NORMALIZE,
	"status": ENUMERATE,
	"prosper_rating": ENUMERATE
    }

# Used for SVM output, must be enumerated column
LABEL_COLUMN_NAME = "prosper_rating"
# What type of samples do we want from the label column
# hard code what number corresponds to each class in the
# resulting libsvm file
SET_LABELS = {"AA":0, "A":1, "B":2, "C":3, "D":4, "E":5, "HR":6}
TRAIN_PERC = 50
#######################################################
#######################################################
#######################################################

def main():
    """
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", type=str, help="Path to CSV file")
    parser.add_argument("--svm", action="store_true", help="Create file formatted for libsvm")
    parser.add_argument("--train", action="store_true", help="Create train/test files for libsvm")
    args = parser.parse_args()
    
    if(not os.path.exists(args.csv_file)):
        print("Could not find CSV file directory")
        exit(1)
        
    # Read column data from CSV file
    column_table, row_number = parse_csv_file(args.csv_file)
    
    # Process the columns we want
    output_columns = {}
    for column_name,method in data_configuration.items():
        if(column_table.get(column_name) is not None):
            if(method == NORMALIZE):
                try:
                    output_columns[column_name] = standardize_column(column_table[column_name])                    
                    output_columns[column_name] = normalize_column(column_table[column_name])
                except Exception as e:
                    print("Error on column", column_name, e)
            elif(method == CATEGORIZE):
                for new_name, new_column in categorize_column(column_table[column_name]).items():
                    output_columns[new_name] = new_column
            elif(method == NOTHING):
                output_columns[column_name] = column_table[column_name]
            elif(method == ENUMERATE):
                output_columns[column_name] = enumerate_column(args.csv_file, column_table[column_name], column_name)
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
    
    if(args.svm):
        format_for_libsvm(args.csv_file, row_number, output_columns)
    
    if(args.svm and args.train):
        create_test_train_files(args.csv_file + ".libsvm")
    
def create_test_train_files(svm_file_path):
    """
    """
    num_rows = 0
    with open(svm_file_path, 'r', encoding="utf8") as svm_in_f:
        for line in svm_in_f:
            num_rows += 1  
    
    num_train_rows = int((TRAIN_PERC/100) * num_rows)
    with open(svm_file_path, 'r', encoding="utf8") as svm_in_f:  
        with open(svm_file_path + ".train.libsvm", 'w', encoding="utf8") as svm_out_train:  
            with open(svm_file_path + ".test.libsvm", 'w', encoding="utf8") as svm_out_test:
                for idx,line in enumerate(svm_in_f):
                    if(idx < num_train_rows):
                        svm_out_train.write(line)
                    else:
                        svm_out_test.write(line)
            
def normalize_column(column):
    """ Normalize column data on a scale of [-1,1]
    """
    max_value = 0
    min_value = 0
    
    # Convert to floats
    for idx,value in enumerate(column):
        try:
            column[idx] = float(value.strip("% "))
        except:
            break
    
    # Find max and min
    max_value = max(column)
    min_value = min(column)

    # Normalize each value
    # (value - min)/(max - min)
    for idx,value in enumerate(column):
        column[idx] = round((value - min_value)/(max_value - min_value),4)
        #column[idx] = round((2*value - max_value - min_value)/(max_value - min_value),4)
    
    return column

def standardize_column(column):
    """ Standardize column data
    """
    # Convert to floats
    for idx,value in enumerate(column):
        try:
            column[idx] = float(value.strip("% "))
        except:
            break
            
    # Find mean and std dev
    mean = statistics.mean(column)
    stddev = statistics.stdev(column)

    for idx,value in enumerate(column):
        column[idx] = round((value - mean)/stddev,4)
    
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

def enumerate_column(csv_file, column, column_name):
    """ Change a column with discrete values to numerical representations
    """
    # Get set of unique values
    discrete_values = set()
    for value in column:
        discrete_values.add(value)
        
    with open(csv_file + "." + column_name + ".legend.txt", "w") as f:
        for label,discrete_value in enumerate(discrete_values):
            f.write(str(label) + ":" + discrete_value + "\n")
        
    for label,discrete_value in enumerate(discrete_values):
        for idx,value in enumerate(column):
            if(value == discrete_value):
                column[idx] = label

    return column    

def format_for_libsvm(csv_file, row_number, output_columns):
    """lib svm format: <label> <feature_idx>:<feature_value> <feature_idx>:<feature_value> ...
    """
    # Read the legend that was created from the "enumerate_column" function.
    label_legend = {}
    with open(csv_file + "." + LABEL_COLUMN_NAME + ".legend.txt", "r") as f:
        for line in f:
            label_key, label_value = line.split(":", 1)
            label_legend[int(label_key)] = label_value.strip()
            
    header_list = [LABEL_COLUMN_NAME]
    column_number = len(output_columns.keys())
    for column_name in output_columns.keys():
        if(column_name != LABEL_COLUMN_NAME):
            header_list.append(column_name)
        
    with open(csv_file + ".libsvm", 'w', encoding="utf8") as f:         
        for row in range(row_number):
            column_idx = 0
            for feature_num,header in enumerate(header_list):
                if(feature_num == 0):
                    if(label_legend[output_columns[header][row]] not in SET_LABELS.keys()): break
                    #f.write(str(output_columns[header][row]))     
                    f.write(str(SET_LABELS[label_legend[output_columns[header][row]]]))
                else:
                    f.write(str(feature_num) + ":" + str(output_columns[header][row]))
                column_idx += 1
                if(column_idx == column_number):
                    f.write("\n")
                else:
                    f.write(" ")

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