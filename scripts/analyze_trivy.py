import json

file = "trivy-report.json"

with open(file) as f:
    data = json.load(f)

total = 0
critical = 0
high = 0

for result in data.get("Results", []):
    for v in result.get("Vulnerabilities", []):
        total += 1
        if v.get("Severity") == "CRITICAL":
            critical += 1
        if v.get("Severity") == "HIGH":
            high += 1

print("=== TRIVY REPORT ===")
print(f"Total vulnerabilities: {total}")
print(f"Critical: {critical}")
print(f"High: {high}")
