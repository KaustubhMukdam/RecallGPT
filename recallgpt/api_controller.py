from memory_manager import MemoryManager, get_relevant_history
from llm_interface import LLMInterface

memory = MemoryManager("recallgpt.db")
llm = LLMInterface(model_name="qwen2.5-coder:1.5b")

def chat(thread_id, usermessage):
    memory.add_message(thread_id, "user", usermessage)
    
    # Get relevant history
    relevant_history = memory.get_hybrid_matches_with_token_limit(thread_id, usermessage, top_k=5, max_tokens=2000)
    
    # Build prompt
    prompt = ""
    for role, content in relevant_history:
        prompt += f"{role}: {content}\n"
    prompt += f"User: {usermessage}\n"
    
    # Generate response
    response = llm.generate(prompt)
    memory.add_message(thread_id, "assistant", response)
    
    # Log the retrieval
    token_count = memory.count_tokens(prompt)
    memory.logger.log_retrieval(
        thread_id=thread_id,
        query=usermessage,
        retrieved_count=len(relevant_history),
        token_count=token_count,
        response_length=len(response),
        retrieval_method="hybrid_token_limited",
        context_msgs=relevant_history
    )
    
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
        print(f"Started new thread '{choice}' (id: {thread_id}). Type 'exit' to quit.")

    while True:
        userinput = input("You: ").strip()
        if userinput.lower() in ["exit", "quit", "bye"]:
            print("Exiting RecallGPT. Conversation memory saved.")
            break
        resp = chat(thread_id, userinput)
        print(f"RecallGPT: {resp}")
