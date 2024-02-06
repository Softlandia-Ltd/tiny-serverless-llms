cd /home/site/wwwroot/

if [ -d "llama.cpp" ]; then
    cd llama.cpp
    git pull
    make clean
    make
    cd ..
else
    git clone https://github.com/ggerganov/llama.cpp.git
    cd llama.cpp
    make
    cd ..  
fi

if [ -e "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    echo 'tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf already exists' >&2
else
    curl -L -o tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf?download=true
fi

if [ -e "qwen2-beta-0_5b-chat-q8_0.gguf" ]; then
    echo 'qwen2-beta-0_5b-chat-q8_0.gguf already exists' >&2
else
    curl -L -o qwen2-beta-0_5b-chat-q8_0.gguf https://huggingface.co/Qwen/Qwen1.5-0.5B-Chat-GGUF/resolve/main/qwen2-beta-0_5b-chat-q8_0.gguf?download=true
fi