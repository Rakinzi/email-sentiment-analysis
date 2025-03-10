import openai
import os

# Set your OpenAI API key either directly or via the OPENAI_API_KEY environment variable.
openai.api_key = os.getenv(
    "OPENAI_API_KEY",
    "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",
)


def test_openai():
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say this is a test"}],
            temperature=7,
            max_tokens=150
        )
        print("OpenAI API is working. Response:")
        print(response.choices[0].message.content)
    except Exception as e:
        print("Error testing OpenAI API:", e)


if __name__ == "__main__":
    test_openai()
