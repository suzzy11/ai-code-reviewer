def generate_report(functions, classes):
    total = len(functions) + len(classes)
    documented = 0

    for f in functions:
        if f["docstring"]:
            documented += 1

    for c in classes:
        if c["docstring"]:
            documented += 1

    coverage = (documented / total) * 100 if total > 0 else 0

    print("\n-------- DOCSTRING REPORT --------")
    print(f"Total Functions + Classes: {total}")
    print(f"With Docstrings: {documented}")
    print(f"Coverage: {coverage:.2f}%")
    print("---------------------------------\n")
