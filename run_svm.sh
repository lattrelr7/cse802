#!/usr/bin/sh
SVM_PATH="/cygdrive/c/Users/ryan/OneDrive/MSU/CSE881/libs/libsvm-3.20"
DATA_SET_PATH="/cygdrive/c/Users/ryan/OneDrive/MSU/CSE802/project/test/predict_subgrade"
CONFUSION_SCRIPT="/cygdrive/c/Users/ryan/workspace/git/cse802/calc_confusion.py"

TRAIN_FILE=$1
TEST_FILE=$2

SVM_TRAIN="$SVM_PATH/svm-train.exe"
SVM_PREDICT="$SVM_PATH/svm-predict.exe"
MODEL_FILE="$SVM_PATH/model2.out"
RESULTS_FILE="$SVM_PATH/results2.txt"

run_svm() {
#echo $SVM_TRAIN -t 2 -c $1 -g $2 -w0 5 "$DATA_SET_PATH/$TRAIN_FILE" $MODEL_FILE
#$SVM_TRAIN -t 2 -c $1 -g $2 -w0 5 "$DATA_SET_PATH/$TRAIN_FILE" $MODEL_FILE
echo $SVM_TRAIN -t 2 -c $1 -g $2 "$DATA_SET_PATH/$TRAIN_FILE" $MODEL_FILE
$SVM_TRAIN -t 2 -c $1 -g $2 "$DATA_SET_PATH/$TRAIN_FILE" $MODEL_FILE
#echo $SVM_TRAIN -t 0 -w7 5 "$DATA_SET_PATH/$TRAIN_FILE" MODEL_FILE
#$SVM_TRAIN -t 0 -w7 5 "$DATA_SET_PATH/$TRAIN_FILE" MODEL_FILE
$SVM_PREDICT "$DATA_SET_PATH/$TEST_FILE" MODEL_FILE $RESULTS_FILE
python3 $CONFUSION_SCRIPT "$DATA_SET_PATH/$TEST_FILE" $RESULTS_FILE
}

run_svm 0.5 0.5

