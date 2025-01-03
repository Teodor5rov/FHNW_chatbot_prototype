import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment.")

    client = OpenAI(api_key=api_key)

    dataset_file = "test_dataset.json"
    results_file = "evaluation_results.json"
    chatbot_url = "http://localhost:5000/api/chat"
    num_iterations = 7

    with open(dataset_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    system_prompt = """Your task is to analyze a conversation between a user and a chatbot assistant to evaluate whether the chatbot's response is correct.
To make this determination, you will be provided with the correct information.
If the chatbot's response includes the correct information mark it as correctly responded. If it does not, mark it as incorrect."""

    evaluation_results = []
    query_stats = {}
    total_evaluations = 0
    correct_count = 0

    total_steps = len(dataset) * num_iterations

    with tqdm(total=total_steps, desc="Evaluating queries", ncols=150) as pbar:
        for item in dataset:
            query = item["query"]
            correct_answer = item["correct_response"]

            if query not in query_stats:
                query_stats[query] = {"correct": 0, "total": 0}

            for i in range(num_iterations):
                pbar.set_description(f"Processing: {query[:80] + '...' if len(query) > 80 else query} (Iteration {i+1}/{num_iterations})")

                payload = {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": "Welcome to FHNW! I'm your chatbot assistant, and I'm here to help answer any questions you may have about our university. Feel free to ask me about our programs, services, or research opportunities. How can I assist you today?"
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ]
                }

                chatbot_response = ""
                try:
                    response = requests.post(
                        chatbot_url,
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(payload),
                        stream=True
                    )

                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith("data: "):
                            data_str = line[len("data: "):]
                            if data_str != "[DONE]":
                                try:
                                    chunk_json = json.loads(data_str)
                                    chatbot_response += chunk_json.get("text", "")
                                except json.JSONDecodeError:
                                    pass

                    evaluation = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {
                                "role": "user",
                                "content": (
                                    f"User query:\n{query}\n\n"
                                    f"Correct information:\n{correct_answer}\n\n"
                                    f"Chatbot assistant response:\n{chatbot_response}"
                                )
                            }
                        ],
                        max_tokens=8000,
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "correctly_responded_schema",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "correctly_responded": {"type": "boolean"}
                                    },
                                    "required": ["correctly_responded"],
                                    "additionalProperties": False
                                },
                                "strict": True
                            }
                        }
                    )

                    if hasattr(evaluation, 'choices'):
                        evaluation_json = evaluation.choices[0].message.content
                    else:
                        raise ValueError("Unexpected response format: missing 'choices' attribute.")

                    evaluation_data = json.loads(evaluation_json)
                    correctly_responded = evaluation_data.get("correctly_responded", False)

                except Exception as e:
                    print(f"Error while processing query '{query}': {e}")
                    chatbot_response = "ERROR"
                    correctly_responded = False

                evaluation_results.append({
                    "query": query,
                    "correct_response": correct_answer,
                    "chatbot_response": chatbot_response,
                    "evaluation": correctly_responded
                })

                query_stats[query]["total"] += 1
                total_evaluations += 1
                if correctly_responded:
                    query_stats[query]["correct"] += 1
                    correct_count += 1

                pbar.update(1)

    if total_evaluations > 0:
        overall_accuracy = 100.0 * correct_count / total_evaluations
    else:
        overall_accuracy = 0.0

    output_data = {
        "evaluation_results": evaluation_results,
        "overall_stats": {
            "total_evaluations": total_evaluations,
            "correct_count": correct_count,
            "overall_accuracy": overall_accuracy
        },
        "per_query_stats": {}
    }

    for q, stats in query_stats.items():
        q_correct = stats["correct"]
        q_total = stats["total"]
        q_acc = 100.0 * q_correct / q_total if q_total > 0 else 0
        output_data["per_query_stats"][q] = {
            "correct": q_correct,
            "total": q_total,
            "accuracy": q_acc
        }

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print("\n======== Final Statistics ========")
    if total_evaluations > 0:
        print(f"Total correct: {correct_count}/{total_evaluations} ({overall_accuracy:.2f}%)\n")
    else:
        print("No evaluations performed.\n")

    for q, stats in query_stats.items():
        q_correct = stats["correct"]
        q_total = stats["total"]
        q_acc = 100.0 * q_correct / q_total if q_total > 0 else 0
        print(f"Query: {q}\n  Correct: {q_correct}/{q_total} ({q_acc:.2f}%)\n")

if __name__ == "__main__":
    main()
