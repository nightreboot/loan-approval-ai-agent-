from dotenv import load_dotenv 
from app.core.memory import Memories
 
def main():
    load_dotenv()
 
    print("==========================================")
    print("       LOAN APPROVAL AI ASSISTANT         ")
    print("==========================================")
    print("\nType 'exit' at any prompt to quit.\n")
 
    while True:
        user_input = input("You: ").strip()
 
        if user_input.lower() in ("exit", "quit"):
            print("\nAssistant: Thank you for using the Loan Approval AI Assistant. Goodbye!")
            break
 
        response = Memories(user_input)
        print(f"\nAssistant:\n{response}\n")
 
 
if __name__ == "__main__":
    main()