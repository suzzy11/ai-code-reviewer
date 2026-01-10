import json


def export_json(data):
    return json.dumps(data, indent=2)


def export_text(data):
    lines = []
    for item in data:
        lines.append(f"{item['file']} :: {item['function']}")
        lines.append(item["issue"])
        lines.append("-" * 40)
    return "\n".join(lines)
