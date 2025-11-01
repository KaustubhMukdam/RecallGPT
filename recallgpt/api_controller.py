from memory_manager import MemoryManager
from llm_interface import LLMInterface

memory = MemoryManager('recallgpt.db')
llm = LLMInterface(model_name="qwen2.5-coder:1.5b")

def chat(thread_id, user_message):
    memory.add_message(thread_id, "user", user_message)
    history = memory.get_recent_history(thread_id, n=10)
    prompt = "\n".join([f"{role}: {content}" for role, content in history])
    response = llm.generate(prompt)
    memory.add_message(thread_id, "assistant", response)
    return response

if __name__ == "__main__":
    threads = memory.list_threads()
    if threads:
        print("Existing threads:")
        for tid, tname, ttime in threads:
            print(f"{tid}: {tname} (created {ttime})")
    choice = input("Type new thread name or thread id to continue: ")
    if choice.isdigit():
        thread_id = int(choice)
        print(f"Resuming thread id {thread_id}. Type 'exit' to quit.")
    else:
        thread_id = memory.create_thread(choice)
        print(f"Started new thread '{choice}' (id={thread_id}). Type 'exit' to quit.")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit", "/bye"]:
            print("Exiting RecallGPT. Conversation memory saved.")
            break
        resp = chat(thread_id, user_input)
        print(f"RecallGPT: {resp}")
