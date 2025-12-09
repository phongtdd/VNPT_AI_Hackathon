import argparse
import csv


def compute_accuracy(csv_path):
    total = 0
    correct = 0

    with open(f"{csv_path}", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            if row["answer"].strip() == row["ground_truth"].strip():
                correct += 1

    accuracy = correct / total if total > 0 else 0
    return accuracy, correct, total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--c",
        type=str,
        default="val_rag_1.csv",
        help="Path to the CSV file containing predictions and ground truths",
    )
    args = parser.parse_args()

    accuracy, correct, total = compute_accuracy(args.c)
    print(f"Total samples: {total}")
    print(f"Correct predictions: {correct}")
    print(f"Accuracy: {accuracy:.4f}")
