import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


class Agent:
    """
    Robust stateful chat agent using the Vertex AI-compatible google-genai SDK.
    """

    def __init__(
        self,
        project_id: str = os.getenv("GC_PROJECT_ID"),
        location: str = "us-east4",
        model_name: str = "gemini-2.5-flash",
        context: str | None = None,
    ):
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.context = context

        # Initialize Vertex AI client
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
        )

        # Conversation history (Vertex doesn’t support “system” roles)
        self.history: list[types.Content] = []

    # ------------------------------------------------------------------

    def clear_history(self):
        """Clears conversation history."""
        print("[Agent]: Clearing history.")
        self.history = []

    def get_history(self):
        """Returns current conversation history."""
        return self.history

    # ------------------------------------------------------------------

    def prompt(self, user_prompt: str, use_history: bool = True, **kwargs) -> str | None:
        """Send a prompt and return the model’s reply."""
        print(f"\n> User: {user_prompt}  (History: {'On' if use_history else 'Off'})")

        try:
            # Build conversation content
            contents = []
            if use_history and self.history:
                contents.extend(self.history)

            contents.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

            # Build configuration — pass system context here!
            config = types.GenerateContentConfig(
                system_instruction=self.context,  # works in Vertex mode
                **kwargs,
            )

            # Call Vertex model
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            # Extract model text
            if not response.candidates:
                print("[Agent Warning]: No candidates returned.")
                return None

            response_text = response.candidates[0].content.parts[0].text
            print(f"< Model: {response_text}")

            # Update local history (Vertex uses “user” / “model” roles)
            if use_history:
                self.history.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))
                self.history.append(types.Content(role="model", parts=[types.Part(text=response_text)]))

            return response_text

        except Exception as e:
            print(f"[Agent Error]: {e}")
            return None


# ------------------------------------------------------------------

if __name__ == "__main__":
    agent = Agent(context="Your name is Chip, and you are a witty AI assistant.")

    # Stateful conversation
    agent.prompt("My name is Alex. What is your name?")
    agent.prompt("Do you remember my name?")

    # Stateless question
    agent.prompt("What is the speed of light?", use_history=False)

    print("\n" + "=" * 40)
    print("--- Creative mode ---")
    creative_agent = Agent(context="You are a poet.")
    creative_agent.prompt(
        "Write a four-line poem about a computer.",
        temperature=0.9,
        max_output_tokens=512,
    )
