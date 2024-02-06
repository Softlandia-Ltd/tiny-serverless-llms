# Serverless Tiny Language Models

[TinyLlama 4-bit quantized 3 trillion token chat model](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) and [8-bit quantized Qwen 2 beta 0.5B Chat](https://huggingface.co/Qwen/Qwen1.5-0.5B-Chat-GGUF) running on Azure Functions consumption plan.

This project is not intended for production use. It is a technology demonstration to show that it is possible to run a large language model on a cheap and scalable serverless platform.

A demo of the app is available at [https://.azurewebsites.net/](https://.azurewebsites.net/). In the demo, you can enter a prompt and the model will generate a completion.

**Any abuse of the service will result in the service being taken down.**

## Running locally

To run the serverless function locally, please refer to [Azure Functions documentation](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-vs-code-python).

You will need following environment variables:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureSignalRBase": "https://{signal_r_service_name}.service.signalr.net",
    "AzureSignalRAccessKey": "{signal_r_service_key}",
    "MODEL_BASE": "{absolute_path_to_model_directory_including_trailing_slash}",
    "LLAMA_BASE": "{absolute_path_to_llama_binary_directory_including_trailing_slash}"
  }
}
```

Copy your llama.cpp binary to the `LLAMA_BASE` directory and the models to the `MODEL_BASE` directory.

## Deploying to Azure

You'll need the following resources in Azure:

- Azure Functions in Consumption Plan
- Azure SignalR Service in serverless mode

You'll need to set the following application setting in Azure Functions:

`POST_BUILD_SCRIPT_PATH=post_build.sh`
`MODEL_BASE=/home/site/wwwroot/`
`LLAMA_BASE=/home/site/wwwroot/llama.cpp`
`AzureSignalRBase=https://{signal_r_service_name}.service.signalr.net`
`AzureSignalRAccessKey={signal_r_service_key}`

This script will be executed during Oryx build. It is used to build the llama.cpp binary and add the models to the deployment package.

## About [Softlandia](https://softlandia.fi/)

Softlandia is a software consultancy based in Finland. We specialize in AI, especially in generative AI, cloud architecture and IoT and in building software in general, from web applications to embedded systems.

Check out our private GenAI product [YOKOT.AI](https://yokot.ai/) and [blog](https://softlandia.fi/blog).
