import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tf", type=str, help="file with test data (label first column)")
    parser.add_argument("rf", type=str, help="file with results (label first column)")
    args = parser.parse_args()
    
    # Get set of possible classes
    class_types = set()

    actual_classes = []
    with open(args.tf, 'r') as tf:
        for line in tf:
            label = int(line.split()[0])
            actual_classes.append(label)
            class_types.add(label)

    predicted_classes = []
    with open(args.rf, 'r') as rf:
        for line in rf:
            label = int(line.split()[0])
            predicted_classes.append(label)
            
    # Create data struct to keep track of predictions
    confusion_matrix = [[0 for col in range(max(class_types) + 1)] for row in range(max(class_types) + 1)]
        
    for i in range(len(actual_classes)):
        actual_class = actual_classes[i]
        predicted_class = predicted_classes[i]
        confusion_matrix[actual_class][predicted_class] += 1

    for row in confusion_matrix:
        print(row)

if __name__ == "__main__": main()
