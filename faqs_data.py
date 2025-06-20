import json

# Load the original JSON
with open("faqs_data.jsonl", "r", encoding="utf-8") as f:
    data = json.load(f)

# Create a new JSONL file
with open("fixed_faqs_data.jsonl", "w", encoding="utf-8") as outfile:
    # For each category
    for category_name, category_data in data.items():
        # For each question in that category
        for question in category_data["questions"]:
            # Create a training example with the required structure
            example = {
                "contents": [
                    {
                        "role": "user", 
                        "parts": [{"text": question["title"]}]
                    },
                    {
                        "role": "model",
                        "parts": [{"text": question["content"]}]
                    }
                ]
            }
            
            # Write as a single line JSON object
            outfile.write(json.dumps(example, ensure_ascii=False) + "\n")